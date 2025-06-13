from web3 import Web3
import time
import api_keys
import contract

import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

ETH = "0x0000000000000000000000000000000000000000"  # ETH (zero address)
TOKEN_A = Web3.to_checksum_address(contract.CONTRACT_ADDRESS)  # Twój token
USDC = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")  # USDC na Base

# Połączenie z siecią Base
#provider = api_keys.INFURA_HTTP
provider= 'https://base-mainnet.infura.io/v3/'+api_keys.INFURA
w3 = Web3(Web3.HTTPProvider(provider))

if not w3.is_connected():
    raise Exception("Nie udało się połączyć z siecią Base!")

# Dane konta
private_key = api_keys.PRIVATEMM
account = w3.eth.account.from_key(private_key)

# Adresy kontraktów Uniswap
uniswap_router_address = Web3.to_checksum_address("0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24")  # Uniswap V2 Router na Base
uniswap_factory_address = Web3.to_checksum_address("0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6")  # Uniswap V2 Factory

# ABI Uniswap Router
# ABI Uniswap Router
uniswap_router_abi = [
    {
        "inputs": [
            {"internalType": "address", "name": "_factory", "type": "address"},
            {"internalType": "address", "name": "_WETH", "type": "address"}
        ],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "inputs": [],
        "name": "WETH",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
            {"internalType": "uint256", "name": "amountADesired", "type": "uint256"},
            {"internalType": "uint256", "name": "amountBDesired", "type": "uint256"},
            {"internalType": "uint256", "name": "amountAMin", "type": "uint256"},
            {"internalType": "uint256", "name": "amountBMin", "type": "uint256"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "addLiquidity",
        "outputs": [
            {"internalType": "uint256", "name": "amountA", "type": "uint256"},
            {"internalType": "uint256", "name": "amountB", "type": "uint256"},
            {"internalType": "uint256", "name": "liquidity", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# ABI Uniswap Factory
uniswap_factory_abi = [
    {"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"}],
     "name":"getPair","outputs":[{"internalType":"address","name":"pair","type":"address"}],"stateMutability":"view","type":"function"}
]

# ABI ERC-20 (approve)
token_abi = [
    {"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}
]

# Inicjalizacja kontraktów
router_contract = w3.eth.contract(address=uniswap_router_address, abi=uniswap_router_abi)
factory_contract = w3.eth.contract(address=uniswap_factory_address, abi=uniswap_factory_abi)
token_a_contract = w3.eth.contract(address=TOKEN_A, abi=token_abi)
token_b_contract = w3.eth.contract(address=USDC, abi=token_abi)

# Parametry transakcji
amount_a_desired = w3.to_wei(100, 'ether')  # 100 TOKEN_A
amount_b_desired = w3.to_wei(0.002, 'mwei')  # 0.002 USDC (przykład)
slippage = 0.05  # 5% slippage
amount_a_min = int(amount_a_desired * (1 - slippage))  # 5% slippage
amount_b_min = int(amount_b_desired * (1 - slippage))  # 5% slippage
deadline = int(time.time()) + 1200  # 20 minut od teraz

# Aktualny nonce
nonce = w3.eth.get_transaction_count(account.address)

# **Krok 1: Zatwierdzenie tokenów**
def approve_token(token_contract, amount, nonce):
    try:
        tx = token_contract.functions.approve(uniswap_router_address, amount).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': w3.to_wei('0.5', 'gwei')
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Zatwierdzono {amount} dla {token_contract.address}: {tx_hash.hex()}")
        return nonce + 1  # Zwiększamy nonce dla następnej transakcji
    except Exception as e:
        print(f"Błąd podczas zatwierdzania tokenu: {e}")
        return nonce

# Zatwierdzamy TOKEN_A i USDC
nonce = approve_token(token_a_contract, amount_a_desired, nonce)
nonce = approve_token(token_b_contract, amount_b_desired, nonce)

# **Krok 2: Dodanie płynności**
def add_liquidity():
    try:
        gas_estimate = router_contract.functions.addLiquidity(
            TOKEN_A,
            USDC,
            amount_a_desired,
            amount_b_desired,
            amount_a_min,
            amount_b_min,
            account.address,
            deadline
        ).estimate_gas({'from': account.address})

        add_liquidity_tx = router_contract.functions.addLiquidity(
            TOKEN_A,
            USDC,
            amount_a_desired,
            amount_b_desired,
            amount_a_min,
            amount_b_min,
            account.address,
            deadline
        ).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': gas_estimate,
            'gasPrice': w3.to_wei('0.5', 'gwei')
        })

        signed_tx = w3.eth.account.sign_transaction(add_liquidity_tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"Pula stworzona! Hash transakcji: {tx_hash.hex()}")
        return receipt
    except Exception as e:
        print(f"Błąd przy dodawaniu płynności: {e}")
        return None

# **Krok 3: Pobranie adresu poola**
def get_pair_address():
    try:
        pair_address = factory_contract.functions.getPair(TOKEN_A, USDC).call()
        if pair_address == "0x0000000000000000000000000000000000000000":
            print("Pula jeszcze nie istnieje.")
        else:
            print(f"Adres poola: {pair_address}")
    except Exception as e:
        print(f"Błąd przy pobieraniu adresu poola: {e}")

# Dodanie płynności i pobranie adresu poola
add_liquidity_receipt = add_liquidity()
if add_liquidity_receipt:
    get_pair_address()
