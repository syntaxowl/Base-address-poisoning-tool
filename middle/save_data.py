import json
import os
import eel
import re


@eel.expose
def save_keys(klucze_dict):
    file_path = os.path.join(os.path.dirname(__file__), "../api_keys.py")
    
    # Klucze domyślne, które nas interesują
    default_keys = {
        "OKLINK_APIKEY": "",
        "PRIVATEMM": "",
        "BASESCANAPI": "",
        "INFURA": ""
    }

    # Wczytaj istniejące dane
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        for key in default_keys:
            match = re.search(rf"{key}\s*=\s*['\"](.*?)['\"]", content)
            if match:
                default_keys[key] = match.group(1)

    # Nadpisz tylko te, które przyszły z frontendu
    if "kluczApi" in klucze_dict:
        default_keys["OKLINK_APIKEY"] = klucze_dict["kluczApi"]
    if "kluczPrywatny" in klucze_dict:
        default_keys["PRIVATEMM"] = klucze_dict["kluczPrywatny"]
    if "baseKey" in klucze_dict:
        default_keys["BASESCANAPI"] = klucze_dict["baseKey"]
    if "infura" in klucze_dict:
        default_keys["INFURA"] = klucze_dict["infura"]

    # Zapisz z powrotem cały plik
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            for key, value in default_keys.items():
                f.write(f"{key} = '{value}'\n")
        return "Zaktualizowano tylko podane klucze!"
    except Exception as e:
        return f"Błąd: {str(e)}"
    

@eel.expose
def save_contract_address(contract_address):
    file_path = os.path.join(os.path.dirname(__file__), "../contract.py")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"CONTRACT_ADDRESS = '{contract_address}'\n")
            
        return "zapisano!"
    except Exception as e:
        return f"Błąd: {str(e)}"