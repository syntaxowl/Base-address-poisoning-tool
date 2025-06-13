import requests
import os
import time
import json
import api_keys
import  contract
import sys
sys.stdout.reconfigure(encoding='utf-8')



BASESCAN_API_URL = "https://api.basescan.org/api"
BASESCAN_API_KEY = api_keys.BASESCANAPI  # Wstaw swój klucz API Basescan

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_CODE_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "..", "token_code"))
NODE_MODULES_DIR = os.path.join(os.getcwd(), "backend", "node_modules1")
project_path = os.path.join(os.getcwd(), "backend","node_modules1")  # Ścieżka do folderu backend



def verify_contract_source_code(contract_address, main_file, contract_name):
    if contract_address == None:
        contract_address=contract.CONTRACT_ADDRESS
    files = {
        main_file: os.path.join(TOKEN_CODE_DIR, main_file),
        "@openzeppelin/contracts/token/ERC20/ERC20.sol": os.path.join(NODE_MODULES_DIR, "ERC20.sol"),
        "@openzeppelin/contracts/access/Ownable.sol": os.path.join(NODE_MODULES_DIR, "Ownable.sol"),
        "@openzeppelin/contracts/security/Pausable.sol": os.path.join(NODE_MODULES_DIR, "Pausable.sol"),
        "@openzeppelin/contracts/utils/Context.sol": os.path.join(NODE_MODULES_DIR, "Context.sol"),
        "@openzeppelin/contracts/token/ERC20/IERC20.sol": os.path.join(NODE_MODULES_DIR, "IERC20.sol"),
        "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol": os.path.join(NODE_MODULES_DIR, "IERC20Metadata.sol")
    }

    sources = {}
    for file_path, full_path in files.items():
        with open(full_path, "r") as f:
            sources[file_path] = {"content": f.read()}

    standard_json = {
        "language": "Solidity",
        "sources": sources,
        "settings": {
            "optimizer": {"enabled": False, "runs": 200},
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}
        }
    }

    source_code_json = json.dumps(standard_json)

    data = {
        "apikey": BASESCAN_API_KEY,
        "module": "contract",
        "action": "verifysourcecode",
        "contractaddress": contract_address,
        "sourceCode": source_code_json,
        "codeformat": "solidity-standard-json-input",
        "contractname": f"{main_file}:{contract_name}",
        "compilerversion": "v0.8.9+commit.e5eed63a",
        "optimizationUsed": "0",
        "runs": "200",
        "licenseType": "3"  # MIT
    }

    response = requests.post(BASESCAN_API_URL, data=data)
    result = response.json()

    if result["status"] == "1":
        guid = result["result"]
        return {"status": "success", "message": f"Kod przesłany. GUID: {guid}", "guid": guid}
    else:
        return {"status": "error", "message": f"Błąd: {result['message']} - {result['result']}"}


def check_verification_status(guid):
    
    params = {
        "apikey": BASESCAN_API_KEY,
        "guid": guid,
        "module": "contract",
        "action": "checkverifystatus"
    }

    response = requests.get(BASESCAN_API_URL, params=params)
    if response.status_code == 200:
        result = response.json()
        return {"status": result["status"], "message": result["message"], "result": result["result"]}
    else:
        return {"status": "error", "message": f"Błąd HTTP: {response.status_code} - {response.text}"}
    

