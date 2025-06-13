import requests
import time
from collections import defaultdict
import csv
import api_keys as api_keys
import threading

from backend.source_destinantion.filters import have_label
from backend.source_destinantion.filters import *
import sys
from backend.stats.database import *
sys.stdout.reconfigure(encoding='utf-8')
# Konfiguracja TEST

API_KEY = api_keys.OKLINK_APIKEY
CHAIN_SHORT_NAME = "base"
TOKEN_CONTRACT = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
PROTOCOL_TYPE = "token_20"
#FILENAME = "adresses_for_test.txt"
MINIMAL_TRANSACTIONS = 4
MINIMAL_AMOUNT_SENDED = 2200
RESULTS_FILENAME = "results.csv"

# Funkcja analizy transakcji w tle
@eel.expose
def analyze_transactions(input_file, output_csv, min_transactions, min_amount_sended):
    def run_in_background():
        try:
            with open(input_file, "r") as file:
                addresses = [line.strip() for line in file.readlines()]
            with open(output_csv, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Source Address", "Destination Address", "Transactions Count", "Total Sent", "Has Label"])
            for address in addresses:
                get_transactions(address, int(min_transactions), float(min_amount_sended), check_labels=True)
                time.sleep(0.5)
            result = f"Zakończono analizę. Wyniki w {output_csv}"
            eel.update_analysis_result(result)  # Aktualizacja GUI po zakończeniu
        except Exception as e:
            eel.update_analysis_result(f"Błąd analizy: {str(e)}")

    # Uruchom w osobnym wątku
    threading.Thread(target=run_in_background, daemon=True).start()
    return "Analiza rozpoczęta w tle..."


# Funkcja do pobierania transakcji dla danego adresu
def get_transactions(address, minimum_transactions, minimum_amount_sended, check_labels=False,database=False):
    url = f"https://www.oklink.com/api/v5/explorer/address/token-transaction-list?chainShortName={CHAIN_SHORT_NAME}&address={address}&protocolType={PROTOCOL_TYPE}&tokenContractAddress={TOKEN_CONTRACT}&isFromOrTo=from"
    headers = {"Ok-Access-Key": API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data["code"] == "0":
            transactions = data["data"][0]["transactionList"]
            address_count = defaultdict(int)
            total_sent_to_address = defaultdict(float)

            if transactions:
                #print(f"\n Adres: {address} - ZNALEZIONO TRANSAKCJE:")
                for tx in transactions:
                    if tx["isFromContract"] == True or tx["isToContract"] == True:
                        continue
                    else:
                        recipient = tx["to"]
                        address_count[recipient] += 1
                        amount = float(tx["amount"]) if tx["amount"] else 0.0
                        total_sent_to_address[recipient] += amount
                        '''
                        print(f"  Tx ID: {tx['txId']}")
                        print(f"  Od: {tx['from']}")
                        print(f"  Do: {tx['to']}")
                        print(f"  Ilosc: {tx['amount']} {tx.get('symbol', 'UNKNOWN')}")
                        print(f"  Oplata TX: {tx.get('txFee', 'Brak danych')} ETH")
                        print(f"  Status: {tx.get('state', 'Brak danych')}\n")
                        '''
                print(f"\n Adres: {address} - ZNALEZIONO TRANSAKCJE:\n **Podsumowanie transakcji do adresow:**") if len(address_count) !=0 else print(f"\n Adres: {address} - NIE ZNALEZIONO TRANSAKCJE:")
                #print("\n **Podsumowanie transakcji do adresow:**")
                for addr in address_count:
                    # Sprawdzamy warunki
                    has_label = have_label(addr) if check_labels else False
                    meets_criteria = (address_count[addr] > minimum_transactions and 
                                    total_sent_to_address[addr] > minimum_amount_sended)
                    
                    # Zapisujemy w locie, jesli adres ma etykiete lub spelnia kryteria
                    if has_label or meets_criteria:
                        print(f"   {addr}: {address_count[addr]} transakcji, laczna wartosc: {total_sent_to_address[addr]} {transactions[0].get('symbol', 'UNKNOWN')} {'(z etykieta)' if has_label else ''}")
                        save_to_file([(address, addr, address_count[addr], total_sent_to_address[addr], has_label)])
                        if database:
                            source_id=get_source_id(address)# czy napewno dobry argument
                            add_destination_address(source_id, addr)
            else:
                print(f"Brak transakcji dla {address}")
        else:
            print(f" Blad API dla adresu {address}: {data['msg']}")
    else:
        print(f" Blad HTTP {response.status_code} dla adresu {address}: {response.text}")

# Funkcja zapisu do CSV w locie
def save_to_file(results):
    if results:
        with open(RESULTS_FILENAME, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for row in results:
                writer.writerow(row)



'''
# Naglowek pliku CSV (z dodatkowa kolumna dla etykiety)
with open(RESULTS_FILENAME, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Source Address", "Destination Address", "Transactions Count", "Total Sent", "Has Label"])

# Wczytanie adresow z pliku i przetwarzanie
with open(FILENAME, "r") as file:
    addresses = [line.strip() for line in file.readlines()]

print(f" Sprawdzanie {len(addresses)} adresow...\n")

for address in addresses:
    get_transactions(address, MINIMAL_TRANSACTIONS, MINIMAL_AMOUNT_SENDED, check_labels=True)
    time.sleep(0.5)  # Ograniczenie liczby zapytań do API (1s opoźnienia)

print(f"\n Wyniki zapisano do {RESULTS_FILENAME}")
'''