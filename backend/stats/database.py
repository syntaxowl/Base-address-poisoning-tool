# database.py
import sqlite3

# Globalne połączenie do bazy danych
conn = sqlite3.connect("adresses.db")
cursor = conn.cursor()

# Tworzenie tabel
cursor.execute('''
    CREATE TABLE IF NOT EXISTS source_addresses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT NOT NULL UNIQUE
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS destination_addresses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER,
        dest_address TEXT NOT NULL UNIQUE,
        FOREIGN KEY (source_id) REFERENCES source_addresses (id)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS vanity_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dest_id INTEGER,
        vanity_address TEXT NOT NULL UNIQUE,
        private_key TEXT NOT NULL,
        FOREIGN KEY (dest_id) REFERENCES destination_addresses (id)
    )
''')

# Funkcje dla source_addresses
def add_source_address(address):
    cursor.execute("INSERT OR IGNORE INTO source_addresses (address) VALUES (?)", (address,))
    conn.commit()
    return get_source_id(address)

def get_source_id(address):
    cursor.execute("SELECT id FROM source_addresses WHERE address = ?", (address,))
    result = cursor.fetchone()
    return result[0] if result else None

def source_address_exists(address):
    cursor.execute("SELECT COUNT(*) FROM source_addresses WHERE address = ?", (address,))
    return cursor.fetchone()[0] > 0

# Funkcje dla destination_addresses
def add_destination_address(source_id, dest_address):
    cursor.execute("""
        INSERT INTO destination_addresses (source_id, dest_address)
        VALUES (?, ?)
    """, (source_id, dest_address))
    conn.commit()
    return get_destination_id(dest_address)

def get_destination_id(dest_address):
    cursor.execute("SELECT id FROM destination_addresses WHERE dest_address = ?", (dest_address,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_destinations_by_source(source_id):
    cursor.execute("SELECT dest_address FROM destination_addresses WHERE source_id = ?", (source_id,))
    return [row[0] for row in cursor.fetchall()]

# Funkcje dla vanity_keys
def add_vanity_key(dest_id, vanity_address, private_key):
    cursor.execute("""
        INSERT INTO vanity_keys (dest_id, vanity_address, private_key)
        VALUES (?, ?, ?)
    """, (dest_id, vanity_address, private_key))
    conn.commit()



def get_destination_id(dest_address):
        cursor.execute("SELECT id FROM destination_addresses WHERE dest_address = ?", (dest_address,))
        result = cursor.fetchone()
        return result[0] if result else None

def get_vanity_by_dest(dest_id):
    cursor.execute("""
        SELECT vanity_address, private_key 
        FROM vanity_keys 
        WHERE dest_id = ?
    """, (dest_id,))
    result = cursor.fetchone()
    return result if result else (None, None)

# Funkcja łącząca wszystko (opcjonalna)
def add_all(source_address, dest_address, vanity_address, private_key):
    source_id = add_source_address(source_address)
    dest_id = add_destination_address(source_id, dest_address)
    add_vanity_key(dest_id, vanity_address, private_key)

def get_all_by_source(source_address):
    source_id = get_source_id(source_address)
    if not source_id:
        return []
    dest_addresses = get_destinations_by_source(source_id)
    result = []
    for dest in dest_addresses:
        dest_id = get_destination_id(dest)
        vanity, key = get_vanity_by_dest(dest_id)
        result.append((dest, vanity, key))
    return result

