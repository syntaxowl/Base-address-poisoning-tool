import eel
from backend.token_gen.deployp import deploy_token
import json
import os

@eel.expose

def deploy(name, output_file=None):
    result = deploy_token(name, output_file=None)  # Pobieramy pełny wynik jako słownik
    if result["status"] == "success":
        contract_address = result["address"]
        abi = result["abi"]
        script_dir = os.path.dirname(os.path.abspath(__file__))
        abi_path = os.path.normpath(os.path.join(script_dir,'..', "token_code", f"{name}_abi.json"))
        with open(abi_path, "w") as f:
            json.dump(abi, f)
        print(f"ABI zapisane do: {name}_abi.json")
        return result  # Zwracamy pełny słownik
    else:
        return result  # Zwracamy błąd