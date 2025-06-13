from uniswappy import Uniswap
from web3 import Web3
import api_keys
import contract

# ✅ Połączenie z siecią Base
#provider = api_keys.INFURA_HTTP  # Infura lub Alchemy  dla testó różne
provider = 'https://base-mainnet.infura.io/v3/'+api_keys.INFURA
w3 = Web3(Web3.HTTPProvider(provider))

if not w3.is_connected():
    raise Exception("❌ Nie udało się połączyć z siecią!")

# ✅ Konfiguracja portfela
private_key = api_keys.PRIVATEMM
account = w3.eth.account.from_key(private_key)
address = account.address
print(f"✅ Twój adres: {address}")

# ✅ Adresy kontraktów
TOKEN = Web3.to_checksum_address(contract.CONTRACT_ADDRESS)  # Twój token
ETH = "0x0000000000000000000000000000000000000000"

# ✅ Połączenie z Uniswap API
uniswap = Uniswap(private_key, provider, version=2)  # Uniswap V2

# ✅ 1️⃣ Sprawdzenie, czy pool już istnieje
pair_address = uniswap.get_liquidity_pool(TOKEN, ETH)
if pair_address is not None:
    print(f"✅ Pool już istnieje! Adres: {pair_address}")
else:
    print("🔹 Pool jeszcze nie istnieje. Tworzymy nowy...")

# ✅ 2️⃣ Dodanie płynności (tworzy pool, jeśli go nie ma)
amount_token = Web3.to_wei(1000, 'ether')  # Ilość tokenów
amount_eth = Web3.to_wei(0.000001, 'ether')  # Ilość ETH

print(f"🔹 Dodawanie {amount_token} TOKEN i {amount_eth} ETH do poola...")

tx_hash = uniswap.add_liquidity_eth(
    TOKEN,
    amount_token,
    amount_eth,
    slippage=0.01,  # 1% slippage
    deadline=600  # 10 minut
)

print(f"✅ Płynność dodana! TX: {tx_hash}")
