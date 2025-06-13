import eel
import os
import time
import multiprocessing
import threading
import csv
from eth_hash.auto import keccak
import ecdsa
import math
import sys
from io import StringIO
from coincurve import PrivateKey
from backend.stats.database import *


sys.stdout.reconfigure(encoding='utf-8')


# Funkcje pomocnicze
def keccak256(data):
    return keccak(data)

def private_to_address(private_key):
    sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    vk = sk.verifying_key
    public_key = b"\x04" + vk.to_string()
    return keccak256(public_key)[-20:]

def generate_wallet():
    priv = PrivateKey()
    pub = priv.public_key.format(compressed=False)[1:]  # usuwa 0x04
    address = keccak256(pub)[-20:]
    return address.hex(), priv.to_hex()

def is_valid_vanity_address(address, prefix=None, suffix=None):
    if prefix and not address.startswith(prefix):
        return False
    if suffix and not address.endswith(suffix):
        return False
    return True


def detect_file_type(input_data):
    """Wykrywa, czy dane wejściowe są w formacie TXT czy CSV"""
    lines = input_data.splitlines()
    
    if not lines:  # Jeśli pusty plik
        return "empty"

    # Sprawdź tylko pierwsze 2-3 linie (jeśli są)
    for i in range(min(3, len(lines))):  
        if "," in lines[i] or ";" in lines[i]:  # CSV zazwyczaj zawiera przecinki/średniki
            return "csv"

    return "txt"

def csv_to_map_convertor(input_data):
    reader = csv.reader(StringIO(input_data))
    next(reader)  # Pomijamy nagłówki
    
    address_map = {}  # Słownik: { destination_address: {set of source_addresses} }
    
    for row in reader:
        if len(row) < 2:  # Pomijamy puste wiersze i błędne formaty
            continue
        
        source_address = row[0].strip()
        destination_address = row[1].strip()
        
        if destination_address not in address_map:
            address_map[destination_address] = set()  # Tworzymy zbiór dla destination_address
        
        address_map[destination_address].add(source_address)  # Dodajemy source_address do zbioru
    
    return address_map

def save_to_csv(file_name, fieldnames, data, add_extra_field=False,value_for_extra_field=None):
    # Sprawdzenie, czy plik istnieje
    script_dir = os.path.dirname(os.path.abspath(__file__))
    token_code_dir = os.path.normpath(os.path.join(script_dir, "..",'..', "vanity_results"))
    csv_file_path = os.path.join(token_code_dir, file_name)
    os.makedirs(token_code_dir, exist_ok=True)

    file_exists = os.path.exists(file_name)

    with open(csv_file_path, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Zapisanie nagłówków tylko przy pierwszym zapisie
        if not file_exists:
            writer.writeheader()

        # Jeśli trzeba dodać extra_field, to go dodajemy
        if add_extra_field:
            data["source_address"] = value_for_extra_field # Możesz dostosować wartość

        # Zapisanie danych do pliku
        writer.writerow(data)





# Funkcja aktualizująca status w Eel
@eel.expose
def update_status(status_text):
    return status_text

def worker(queue, prefix, suffix, stop_event, attempts_counter):
    """Pracownik generujący adresy."""
    attempts = 0
    while not stop_event.is_set():
        address, private_key = generate_wallet()
        
        with attempts_counter.get_lock():
            attempts_counter.value += 1
        if is_valid_vanity_address(address, prefix, suffix):
            
            queue.put((address, private_key, attempts))
            stop_event.set()
            break

def print_stats(attempts_counter, prefix, suffix, stop_event, mode, total_addresses=1, current_address=1):
    """Wątek wysyłający statystyki do Eel."""
    start_time = time.time()
    difficulty = 16 ** (len(prefix or "") + len(suffix or ""))

    while not stop_event.is_set():
        time.sleep(1)
        with attempts_counter.get_lock():
            total_attempts = attempts_counter.value
        elapsed_time = time.time() - start_time
        speed = int(total_attempts / elapsed_time) if elapsed_time > 0 else 0
        probability = 1 - math.exp(-total_attempts / difficulty)
        probability_percent = round(probability * 100, 2)
        prob_50 = (difficulty / 2) / speed if speed > 0 else float('inf')

        status_text = (
            f"Status: Running\n"
            f"Mode: {mode}\n"
        )
        if mode == "file":
            status_text += f"Address: {current_address} of {total_addresses}\n"
        status_text += (
            f"Difficulty: {difficulty:,}\n"
            f"Generated: {total_attempts:,} addresses\n"
            f"Speed: {speed:,} addr/s\n"
            f"50% ETA: {int(prob_50) if prob_50 != float('inf') else '?'} sec\n"
            f"Probability: {probability_percent}%\n"
            f"Time elapsed: {elapsed_time:.2f} seconds"
        )
        eel.update_status(status_text)

@eel.expose
def find_vanity_address(mode, input_data, prefix_length, suffix_length, prefix="", suffix="", num_workers=None):
    """Wielowątkowe wyszukiwanie vanity address z różnymi trybami."""
    prefix_length = int(prefix_length)
    suffix_length = int(suffix_length)
    if num_workers is None:
        num_workers = max(1, multiprocessing.cpu_count() - 1)

    if mode == "manual":
        if not prefix and not suffix:
            return {"error": "Podaj prefiks lub sufiks w trybie manualnym"}

        queue = multiprocessing.SimpleQueue()
        stop_event = multiprocessing.Event()
        attempts_counter = multiprocessing.Value('i', 0)
        processes = []

        for _ in range(num_workers):
            p = multiprocessing.Process(target=worker, args=(queue, prefix, suffix, stop_event, attempts_counter))
            p.start()
            processes.append(p)

        stats_thread = threading.Thread(target=print_stats, args=(attempts_counter, prefix, suffix, stop_event, mode))
        stats_thread.start()

        start_time = time.time()
        address, private_key, _ = queue.get()
        elapsed_time = time.time() - start_time

        stop_event.set()
        stats_thread.join()
        for p in processes:
            p.join(timeout=1)
            if p.is_alive():
                p.terminate()
                p.join()

        with attempts_counter.get_lock():
            total_attempts = attempts_counter.value
        speed = int(total_attempts / elapsed_time) if elapsed_time > 0 else 0

        result = {
            "address": f"0x{address}",
            "private_key": private_key,
            "attempts": total_attempts,
            "speed": speed,
            "time": elapsed_time
        }
        return {"success": "Wygenerowano adres", "results": [result]}

    elif mode == "address":
        if not input_data:
            return {"error": "Podaj adres w trybie address"}
        input_data= input_data.lower()
        start_index = 2  # Zawsze pomijamy 2 pierwsze znaki ("0x")
        end_index = start_index + prefix_length 

        prefix = address[start_index : end_index] if prefix_length > 0 else ""
        suffix = input_data[-suffix_length:] if suffix_length > 0 else ""

        queue = multiprocessing.SimpleQueue()
        stop_event = multiprocessing.Event()
        attempts_counter = multiprocessing.Value('i', 0)
        processes = []

        for _ in range(num_workers):
            p = multiprocessing.Process(target=worker, args=(queue, prefix, suffix, stop_event, attempts_counter))
            p.start()
            processes.append(p)

        stats_thread = threading.Thread(target=print_stats, args=(attempts_counter, prefix, suffix, stop_event, mode))
        stats_thread.start()

        start_time = time.time()
        address, private_key, _ = queue.get()
        elapsed_time = time.time() - start_time

        stop_event.set()
        stats_thread.join()
        for p in processes:
            p.join(timeout=1)
            if p.is_alive():
                p.terminate()
                p.join()

        with attempts_counter.get_lock():
            total_attempts = attempts_counter.value
        speed = int(total_attempts / elapsed_time) if elapsed_time > 0 else 0

        result = {
            "address": f"0x{address}",
            "private_key": private_key,
            "attempts": total_attempts,
            "speed": speed,
            "time": elapsed_time,
            "input_address": input_data
        }
        return {"success": "Wygenerowano adres", "results": [result]}

    elif mode == "file":
        output_file = "vanity_eth_results_only.csv"
        output_file1= "vanity_eth_results_with_address.csv"
        if not input_data:
            return {"error": "Nie podano zawartości pliku"}
        
        file_format=detect_file_type(input_data)

        if file_format== 'txt':
            lines = [line.strip() for line in input_data.splitlines() if line.strip()]
            
        elif file_format == 'csv':
           address_map = csv_to_map_convertor(input_data)
           lines = list(address_map.keys())
        elif file_format =='empty':
            return {"error": "Plik jest pusty"}
        
        else:
            return {"error": "Nieobsługiwany format pliku"}

        print("wybrany plik")
        results = []
        total_addresses = len(lines)

        for i, address in enumerate(lines, 0):
            
            print("wszedlem w petlie")
            print(address)
            address = address.lower()
            print(address)

            start_index = 2  # Zawsze pomijamy 2 pierwsze znaki ("0x")
            end_index = start_index + prefix_length 

            prefix = address[start_index : end_index] if prefix_length > 0 else ""
            suffix = address[-suffix_length:] if suffix_length > 0 else ""
            print(suffix, prefix)

            queue = multiprocessing.SimpleQueue()
            stop_event = multiprocessing.Event()
            attempts_counter = multiprocessing.Value('i', 0)
            processes = []
            print("skonfigurowano eventy")

            for _ in range(num_workers):
                p = multiprocessing.Process(target=worker, args=(queue, prefix, suffix, stop_event, attempts_counter))
                p.start()
                processes.append(p)
            
            
            stats_thread = threading.Thread(target=print_stats, args=(attempts_counter, prefix, suffix, stop_event, mode, total_addresses, i))
            stats_thread.start()

            
            start_time = time.time()
            gen_address, private_key, _ = queue.get()
            elapsed_time = time.time() - start_time

            

            stop_event.set()
            stats_thread.join()
            for p in processes:
                p.join(timeout=1)
                if p.is_alive():
                    p.terminate()
                    p.join()

            
            with attempts_counter.get_lock():
                total_attempts = attempts_counter.value
            speed = int(total_attempts / elapsed_time) if elapsed_time > 0 else 0
            vanity_address=f"0x{gen_address}"
            result = {
                "destination_address": address,
                "vanity_address": vanity_address,
                "private_key": private_key,
                "attempts": total_attempts,
                "speed": speed,
                "time": elapsed_time
                
            }
            print(f"znaleziono plik, {vanity_address}")
            fieldnames_1 = ["destination_address", "vanity_address", "private_key", "attempts", "speed", "time"]
            save_to_csv(output_file, fieldnames_1, result)
            dest_id=get_destination_id(address)
            add_vanity_key(dest_id, vanity_address, private_key)
            if file_format=='csv':
            # Zapis do drugiego pliku (z dodatkowym polem na 1 miejscu)
                fieldnames_2 = ["source_address", "destination_address", "vanity_address", "private_key", "attempts", "speed", "time"]
                for source_addresses in address_map[address]:
                    value_for_extra_field=source_addresses
                    save_to_csv(output_file1, fieldnames_2, result, add_extra_field=True,value_for_extra_field=value_for_extra_field)

        return {"success": f"Wyniki zapisane do {output_file}", "results": results}

    else:
        return {"error": "Nieznany tryb działania"}
