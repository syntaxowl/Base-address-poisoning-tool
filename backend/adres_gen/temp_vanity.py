import multiprocessing
from eth_hash.auto import keccak
import ecdsa
import sys
from coincurve import PrivateKey
import csv
import os




sys.stdout.reconfigure(encoding='utf-8')

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


def find_vanity_address( input_data, prefix_length, suffix_length):
    """Wielowątkowe wyszukiwanie vanity address z różnymi trybami."""
    prefix_length = int(prefix_length)
    suffix_length = int(suffix_length)
    
    num_workers = max(1, multiprocessing.cpu_count() - 1)


    if not input_data:
        return {"error": "Podaj adres w trybie address"}
    input_data= input_data.lower()
    prefix = input_data[:prefix_length] if prefix_length > 0 else ""
    suffix = input_data[-suffix_length:] if suffix_length > 0 else ""

    queue = multiprocessing.SimpleQueue()
    stop_event = multiprocessing.Event()
    attempts_counter = multiprocessing.Value('i', 0)
    processes = []

    for _ in range(num_workers):
        p = multiprocessing.Process(target=worker, args=(queue, prefix, suffix, stop_event, attempts_counter))
        p.start()
        processes.append(p)

    

    
    address, private_key, _ = queue.get()
    stop_event.set()
    
    for p in processes:
        p.join(timeout=1)
        if p.is_alive():
            p.terminate()
            p.join()

    
    result = {
        "address": f"0x{address}",
        "private_key": private_key,
        "input_address": input_data
    }

    file_name = "monitor_adresses.csv"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    token_code_dir = os.path.normpath(os.path.join(script_dir, "..",'..', "monitor_atack_adresses"))
    csv_file_path = os.path.join(token_code_dir, file_name)

    # Zapisz słownik do pliku CSV
    with open(file_name, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=result.keys())
        writer.writeheader()
        writer.writerow(result)

    return address
