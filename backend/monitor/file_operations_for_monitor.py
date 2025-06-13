
import sys
import csv
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
'''
def load_addresses_from_file(filename):
    try:
        with open(filename, 'r') as f:
            # Wczytujemy adresy, usuwamy białe znaki i konwertujemy na lowercase
            addresses = {line.strip().lower() for line in f if line.strip()}
        print(f"Wczytano {len(addresses)} adresów z pliku {filename}")
        return addresses
    except FileNotFoundError:
        print(f"Plik {filename} nie znaleziony, tworzę pusty zbiór.")
        return set()
    '''

def load_addresses_from_file(input_source=None):
    """
    Wczytuje adresy z pliku lub stringu.
    :param input_source: Ścieżka do pliku (str) lub zawartość pliku (str). Jeśli None, zwraca pusty zbiór.
    :return: Zbiór adresów (set).
    """
    addresses = set()

    if not input_source:
        print("Brak źródła danych, zwracam pusty zbiór.")
        return addresses

    try:
        # Jeśli input_source to ścieżka do pliku
        if isinstance(input_source, str) and '\n' not in input_source and input_source.endswith(('.txt', '.csv')):
            with open(input_source, 'r', encoding='utf-8') as f:
                addresses = {line.strip().lower() for line in f if line.strip()}
            print(f"Wczytano {len(addresses)} adresów z pliku {input_source}")
        # Jeśli input_source to zawartość pliku (string z liniami)
        else:
            addresses = {line.strip().lower() for line in input_source.splitlines() if line.strip()}
            print(f"Wczytano {len(addresses)} adresów z danych wejściowych")
        
        return addresses
    except FileNotFoundError:
        print(f"Plik {input_source} nie znaleziony, zwracam pusty zbiór.")
        return set()
    except Exception as e:
        print(f"Błąd podczas wczytywania danych: {e}")
        return set()
'''
def load_from_to_vanity_map(csv_file):
    
    from_to_vanity_map = defaultdict(dict)  # Słownik z domyślnymi słownikami jako wartościami
    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Pomijamy nagłówek
        for row in reader:
            from_address = row[0].lower()
            to_address = row[1].lower()
            vanity_address = row[2].lower()
            from_to_vanity_map[from_address][to_address] = vanity_address  # Wewnętrzny słownik
    print("przed returnem")
    return dict(from_to_vanity_map)
'''
from collections import defaultdict
import csv

def load_from_to_vanity_map(csv_file):
    from_to_vanity_map = defaultdict(dict)  # Słownik z domyślnymi słownikami jako wartościami
    
    try:
        with open(csv_file, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            
            # Sprawdzam, czy plik ma nagłówek
            try:
                header = next(reader)  # Pomijam nagłówek
                if len(header) < 3:
                    print(f"Błąd: Nagłówek pliku {csv_file} ma mniej niż 3 kolumny: {header}")
                    return dict(from_to_vanity_map)  # Zwracamy pusty słownik w przypadku błędu
            except StopIteration:
                print(f"Błąd: Plik {csv_file} jest pusty lub nie ma nagłówka.")
                return dict(from_to_vanity_map)

            # Przetwarzamy wiersze
            for i, row in enumerate(reader, start=2):  # Start=2, bo liczymy od wiersza po nagłówku
                if len(row) < 3:
                    print(f"Błąd w wierszu {i} pliku {csv_file}: Za mało kolumn ({len(row)} zamiast 3): {row}")
                    continue  # Pomijamy błędny wiersz
                try:
                    from_address = row[0].lower()
                    to_address = row[1].lower()
                    vanity_address = row[2].lower()
                    from_to_vanity_map[from_address][to_address] = vanity_address
                except AttributeError as e:
                    print(f"Błąd w wierszu {i} pliku {csv_file}: Nieprawidłowe dane (oczekiwano stringów): {row}. Szczegóły: {e}")
                    continue

    except FileNotFoundError:
        print(f"Błąd: Plik {csv_file} nie istnieje.")
        return dict(from_to_vanity_map)  # Zwracamy pusty słownik
    except PermissionError:
        print(f"Błąd: Brak uprawnień do odczytu pliku {csv_file}.")
        return dict(from_to_vanity_map)
    except UnicodeDecodeError:
        print(f"Błąd: Problem z kodowaniem pliku {csv_file}. Sprawdź, czy jest w UTF-8.")
        return dict(from_to_vanity_map)
    except Exception as e:
        print(f"Błąd: Nieoczekiwany problem podczas odczytu pliku {csv_file}: {e}")
        return dict(from_to_vanity_map)

    print("Przed returnem - wczytano dane poprawnie")
    return dict(from_to_vanity_map)

