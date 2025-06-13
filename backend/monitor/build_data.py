import csv
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Funkcja do wczytania danych i zbudowania hashmapy
def build_address_map(csv_file):
    if csv_file ==None:
        return {}
    else:
        address_map = {}
        with open(csv_file, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                input_address = row[0]
                address = row[1]
                if input_address not in address_map:  # Dodaj tylko jeśli nowy
                    address_map[input_address] = address
        return address_map
