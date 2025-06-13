# backend/main.py
import eel
import sqlite3
from datetime import datetime, timedelta
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def _get_connection():
    return sqlite3.connect("stats.db")

def create_table():
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS log_counts (
                hour TEXT,
                log_type TEXT,
                count INTEGER,
                PRIMARY KEY (hour, log_type)
            )
        """)
        conn.commit()

def insert_log(log_type, count=1, hour=None):
    with _get_connection() as conn:
        cursor = conn.cursor()
        hour = hour or datetime.now().strftime('%Y-%m-%d %H:00')
        cursor.execute("""
            UPDATE log_counts
            SET count = count + ?
            WHERE hour = ? AND log_type = ?
        """, (count, hour, log_type))
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO log_counts (hour, log_type, count)
                VALUES (?, ?, ?)
            """, (hour, log_type, count))
        conn.commit()

@eel.expose
def get_stats_by_interval(after, before, interval):
    print(f"Pobieranie statystyk: {after} - {before}, interwał: {interval}")
    try:
        # Konwersja dat ISO 8601 (z 'Z') do obiektu datetime
        after_dt = datetime.fromisoformat(after.replace('Z', '+00:00'))
        before_dt = datetime.fromisoformat(before.replace('Z', '+00:00'))
        
        # Formatowanie do postaci używanej w bazie danych
        after_str = after_dt.strftime('%Y-%m-%d %H:00')
        before_str = before_dt.strftime('%Y-%m-%d %H:59')
    except ValueError as e:
        return json.dumps({"error": f"Nieprawidłowy format daty: {str(e)}"})

    if interval == "hour":
        group_by = "strftime('%Y-%m-%d %H:00', hour)"
        label_format = "%Y-%m-%d %H:00"
    elif interval == "day": 
        group_by = "date(hour)"
        label_format = "%Y-%m-%d"
    elif interval == "week":
        group_by = "strftime('%Y-W%W', hour)"
        label_format = "%Y-W%V"
    elif interval == "month":
        group_by = "strftime('%Y-%m', hour)"
        label_format = "%Y-%m"
    else:
        return json.dumps({"error": "Invalid interval"})

    with _get_connection() as conn:
        cursor = conn.cursor()
        
        # Tylko interesujące nas typy logów
        valid_types = ["filtered", "sended"]
        placeholders = ','.join(['?'] * len(valid_types))
        
        query = f"""
            SELECT {group_by} as period, log_type, SUM(count) as total
            FROM log_counts
            WHERE hour >= ? AND hour <= ?
            AND log_type IN ({placeholders})
            GROUP BY {group_by}, log_type
            ORDER BY period, log_type
        """
        
        # Parametry: data początkowa, data końcowa + typy logów
        params = [after_str, before_str] + valid_types
        
        print("Zapytanie SQL:", query)
        print("Parametry:", params)
        
        cursor.execute(query, params)
        
        # Inicjalizacja struktury wyników
        stats = {}
        for row in cursor.fetchall():
            period, log_type, total = row
            log_type = log_type.strip().lower()
            
            if period not in stats:
                stats[period] = { "filtered": 0, "sended": 0}
            
            if log_type in stats[period]:
                stats[period][log_type] = total
        
        # Konwersja do listy
        result = [
            {
                "period": period,
                "filtered": counts["filtered"],
                "sended": counts["sended"]
            }
            for period, counts in sorted(stats.items())
        ]
        
        print("Wynik:", result)
        return json.dumps(result)

def print_db_contents():
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM log_counts")
        for row in cursor.fetchall():
            print(row)




import random
from datetime import datetime, timedelta

def generate_test_data():
    """Generuje testowe dane z ostatnich 6 miesięcy"""
    now = datetime.now()
    start_date = now - timedelta(days=180)  # 6 miesięcy wstecz
    
    current_date = start_date
    while current_date <= now:
        hour = current_date.strftime('%Y-%m-%d %H:00')
        
        # Generuj losowe wartości
        filtered = random.randint(100, 500)
        sended = int(filtered * random.uniform(0.07, 0.21))  # 7-21% of filtered
        
        # Wstaw do bazy
        insert_log("filtered", filtered, hour)
        insert_log("sended", sended, hour)
        
        # Przejdź do następnej godziny
        current_date += timedelta(hours=1)

if __name__ == "__main__":
    create_table()
    generate_test_data()
    print("Wygenerowano testowe dane z ostatnich 6 miesięcy")
    print_db_contents()





'''
if __name__ == "__main__":
    create_table()
    print_db_contents()

    # Testowanie z aktualnymi danymi
    now = datetime.now()
    test_after = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
    test_before = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + 'Z'
    
    print("\n=== Test: Hour (dzisiejsze dane) ===")
    print(json.loads(get_stats_by_interval(test_after, test_before, "hour")))
    
    print("\n=== Test: Day (dzisiejsze dane) ===")
    print(json.loads(get_stats_by_interval(test_after, test_before, "day")))
    '''