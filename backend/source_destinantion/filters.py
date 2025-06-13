## this class will be used to filter addreses for   monitoring


from web3 import Web3
import json
import time
import requests
import json
from datetime import datetime, timedelta
import api_keys as api_keys
import eel
from eth_account import Account
from backend.stats.database import *


import  threading
import sys
sys.stdout.reconfigure(encoding='utf-8')

#Konfiguracja test
INFURA_URL='https://base-mainnet.infura.io/v3/'+api_keys.INFURA
#INFURA_URL = api_keys.INFURA_HTTP
TOKEN_CONTRACT = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
FILENAME = "addresses.txt"
APIKEY=api_keys.OKLINK_APIKEY
CHAIN_SHORT_NAME = "base"  
PROTOCOL_TYPE = "token_20"
TXT_FILE_TO_WRITE_HOLDERS='addressess1.txt'
PRIVATE_KEY=api_keys.PRIVATEMM



web3 = Web3(Web3.HTTPProvider(INFURA_URL))


headers = {
    "Ok-Access-Key": APIKEY
}


def get_address_balance():
    my_address =Account.from_key(PRIVATE_KEY).address
    print(my_address)
    url = f"https://www.oklink.com//api/v5/explorer/address/information-evm?chainShortName=base&address={my_address}"
    response = requests.get(url, headers=headers)
            
    if response.status_code == 200:
                data = response.json()
                return data['data'][0]['balance']
    else: return None


def get_token_holders_list_from_zero(min_amount=10000.0,minimum_transactions=20, last_transaction_days=30):
    total_addresses = 0  # Licznik zapisanych adresów

    # Otwieramy plik raz na poczatku w trybie zapisu (nadpisuje plik)
    with open(TXT_FILE_TO_WRITE_HOLDERS, 'w', encoding='utf-8',buffering=1) as file:
        # Pobieramy dane z API dla każdej strony
        page=0
        x=True
        while x:  # Strona 1 do 1009
            url = f"https://www.oklink.com/api/v5/explorer/token/position-list?chainShortName={CHAIN_SHORT_NAME}&tokenContractAddress={TOKEN_CONTRACT}&limit=50&page={page}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"Przetwarzam strone {page}")
                
                # Sprawdzamy, czy sa dane w odpowiedzi
                position_list = data.get('data', [{}])[0].get('positionList', [])
                if position_list:
                    # Analizujemy i zapisujemy adresy w locie
                    for item in position_list:
                        holding_amount = float(item.get("amount", 0))  # Saldo tokenów
                        address = item["holderAddress"]
                        
                        # Przyklad analizy: zapisujemy tylko adresy z saldem > min_amount
                        if holding_amount < min_amount:
                            x=False
                        
                        if have_label(address):        
                            continue
                    
                        
                                   
                        if not is_transaction_activity_sufficient(address, minimum_transactions, last_transaction_days):
                             continue
                        total_addresses+=1
                        file.write(f"{address}\n")      
                                 
                        
                else:
                    print(f"Brak danych na stronie {page}. Koncze.")
                    break
                page+=1
            else:
                print(f"Blad: {response.status_code} przy stronie {page}. Koncze.")
                break
            

    print(f"Zapisano {total_addresses} adresow z saldem > {min_amount} do pliku {TXT_FILE_TO_WRITE_HOLDERS}.")

def is_transaction_activity_sufficient(address,  minimumTransactions, last_transaction_days): # sprawdzic date pierwszej transakcji?
    # URL API OKLink
    url = f"https://www.oklink.com/api/v5/explorer/address/information-evm?chainShortName={CHAIN_SHORT_NAME}&address={address}"

    # Wyslanie żadania GET
    response = requests.get(url, headers=headers)

    # Przetwarzanie odpowiedzi
    if response.status_code == 200:
        data = response.json()
        
        if data["code"] == "0" and data["data"]:  # Sprawdzamy, czy mamy dane
            info = data["data"][0]  # Pierwszy (i jedyny) wynik
            contract_address = info["contractAddress"]
            transaction_count = int(info["transactionCount"])
            last_transaction_time = info.get("lastTransactionTime")  # Sprawdzamy, czy istnieje

            if contract_address  == True:
                return False
            elif  transaction_count<minimumTransactions:
                return False
            elif last_transaction_time:  
                    transaction_date = datetime.utcfromtimestamp(int(last_transaction_time) / 1000)
                    now = datetime.utcnow()
                    days_ago = now - timedelta(days=last_transaction_days)

                    
                    if days_ago <= transaction_date <= now:
                        return True
                    else:
                        return False

            else:
                    print(" Brak informacji o ostatniej transakcji.")
                    return False
        else:
            print(f" Blad API: {data.get('msg', 'Nieznany blad')}")

    else:
        print(f" Blad HTTP {response.status_code}: {response.text}")

def have_label(address):
    API_URL = "https://www.oklink.com/api/v5/explorer/address/entity-label"
    url = f"{API_URL}?chainShortName={CHAIN_SHORT_NAME}&address={address}&protocolType={PROTOCOL_TYPE}"
        
    response = requests.get(url, headers=headers)
        
    if response.status_code == 200:
        data = response.json()
        if data["code"] == "0" and "data" in data and len(data["data"]) > 0:
            return True  # Ma etykiete
        return False  # Nie ma etykiety (pusta lista lub brak danych)
    return False  # Blad API   




def is_balance_above_minimum(address,min_amount):    
    url = f"https://www.oklink.com/api/v5/explorer/address/token-balance?chainShortName={CHAIN_SHORT_NAME}&address={address}&protocolType={PROTOCOL_TYPE}&tokenContractAddress={TOKEN_CONTRACT}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        token_list = data["data"][0]["tokenList"]

        if not token_list:
            return False
        else:

            holding_amount = float(data["data"][0]["tokenList"][0]["holdingAmount"])
            if holding_amount<min_amount:
                return False
            else:
                return True
    else:
        print(response.status_code)

@eel.expose
def filter_addresses(from_zero, input_file, output_file, min_amount, min_transactions, last_days,database=True):
    def run_in_background():
        try:
            if from_zero:
                get_token_holders_list_from_zero(float(min_amount), int(min_transactions), int(last_days))
                result = f"Zakończono filtrowanie od zera. Wyniki w addressess1.txt"
            else:
                with open(input_file, "r") as file:
                    addresses = [line.strip() for line in file.readlines()]
                with open(output_file, "w") as output:
                    for address in addresses:
                        if have_label(address):
                            continue
                        if not is_balance_above_minimum(address, float(min_amount)):
                            continue
                        if not is_transaction_activity_sufficient(address, int(min_transactions), int(last_days)):
                            continue
                        output.write(f"{address}\n")
                        if database:
                            add_source_address(address)
                result = f"Zakończono filtrowanie. Wyniki w {output_file}"
            eel.update_filter_result(result)  # Aktualizacja GUI po zakończeniu
        except Exception as e:
            eel.update_filter_result(f"Błąd filtrowania: {str(e)}")

    # Uruchom w osobnym wątku
    threading.Thread(target=run_in_background, daemon=True).start()
    return "Filtrowanie rozpoczęte w tle..."



#get_address_balance()