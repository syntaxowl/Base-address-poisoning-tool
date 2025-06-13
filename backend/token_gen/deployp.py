import os
from solcx import compile_source
from web3 import Web3
from eth_account import Account
import api_keys as key
import sys
import logging

sys.stdout.reconfigure(encoding='utf-8')


log_dir = os.path.join(os.getcwd(), "logs", "token_generator_logs")
os.makedirs(log_dir, exist_ok=True)  # Tworzy katalog, jeśli nie istnieje

# Konfiguracja loggerów
log_formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

# Logger dla wszystkich logów
deploy_logger = logging.getLogger("deploy")
deploy_logger.setLevel(logging.INFO)
deploy_handler = logging.FileHandler(os.path.join(log_dir, "deploy.log"), encoding="utf-8")
deploy_handler.setFormatter(log_formatter)
deploy_logger.addHandler(deploy_handler)




def deploy_token(name, output_file=None):
    try:
        # 1. Połączenie z siecią
        #rpc_url = "https://base-sepolia.infura.io/v3/" + key.INFURA
        rpc_url="https://base-mainnet.infura.io/v3/"+key.INFURA
        id=8453                                             ## ustawiać dynamicznie
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise Exception("Nie udało się połączyć z siecią")

        # 2. Konfiguracja konta
        private_key = key.PRIVATEMM
        account = w3.eth.account.from_key(private_key)

        # 3. Wczytanie kodu Solidity
        if output_file is None:
            #solidity_file_path  = os.path.join(os.getcwd(), f"{name}.sol" )  # Ścieżka do folderu backend
            script_dir = os.path.dirname(os.path.abspath(__file__))  # Katalog, w którym znajduje się skrypt
            solidity_file_path = os.path.normpath(os.path.join(script_dir,'..','..', "token_code", f"{name}.sol"))
            #solidity_file_path = os.path.join(os.path.dirname(os.getcwd()), "tocken_code", f"{name}.sol")
            #solidity_file_path = f"{name}.sol"
        else:
            solidity_file_path = output_file

        if not os.path.exists(solidity_file_path):
            raise Exception(f"Plik {solidity_file_path} nie istnieje")

        with open(solidity_file_path, "r") as file:
            solidity_code = file.read()

        # 4. Kompilacja kodu Solidity
        base_dir = os.path.dirname(os.path.abspath(__file__))
        node_modules_path = os.path.join(base_dir,'..', "node_modules", "@openzeppelin", "contracts/")

        compiled_sol = compile_source(
            solidity_code,
            output_values=["abi", "bin"],
            solc_version="0.8.9",
            import_remappings={"@openzeppelin/contracts/": node_modules_path}
        )
        contract_id, contract_interface = list(compiled_sol.items())[0]
        abi = contract_interface["abi"]
        bytecode = contract_interface["bin"]

        # 5. Przygotowanie transakcji
        TokenContract = w3.eth.contract(abi=abi, bytecode=bytecode)
        gas_estimate = TokenContract.constructor().estimate_gas({"from": account.address, "chainId": id})
        txn = TokenContract.constructor().build_transaction({
            "chainId": id,
            "gas": int(gas_estimate * 1.2),
            "gasPrice": int(w3.eth.gas_price * 1.2),
            "nonce": w3.eth.get_transaction_count(account.address),
            "from": account.address
        })

        # 6. Podpisanie i wysłanie transakcji
        signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        contract_address = tx_receipt.contractAddress

        # 7. Zwróć wynik
        message=f"Token {name} wdrożony na adresie: {contract_address}"
        deploy_logger.info(message)
        return {"status": "success", "message": f"Token {name} wdrożony na adresie: {contract_address}", "address": contract_address, "abi": abi}

    except Exception as e:
        return {"status": "error", "message": str(e), "step": "unknown"}

