import os
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
import eel
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# Funkcja do tworzenia folderu z datą
def create_log_folder():
    today = datetime.today().strftime('%Y-%m-%d')  # Formatujemy dzisiejszą datę
    log_dir = os.path.join("logs", today)
    
    # Jeśli folder nie istnieje, tworzymy go
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    return log_dir

# Katalog na logi
log_dir = create_log_folder()

# Konfiguracja loggerów
log_formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

# Logger dla wszystkich logów
all_logger = logging.getLogger("all_logs")
all_logger.setLevel(logging.INFO)
all_handler = logging.FileHandler(os.path.join(log_dir, "all_logs.log"), encoding="utf-8")
all_handler.setFormatter(log_formatter)
all_logger.addHandler(all_handler)

# Logger dla pasujących adresów
matched_logger = logging.getLogger("matched_logs")
matched_logger.setLevel(logging.INFO)
matched_handler = logging.FileHandler(os.path.join(log_dir, "matched_logs.log"), encoding="utf-8")
matched_handler.setFormatter(log_formatter)
matched_logger.addHandler(matched_handler)

# Logger dla wysłanych transakcji
sent_tx_logger = logging.getLogger("sent_tx_logs")
sent_tx_logger.setLevel(logging.INFO)
sent_tx_handler = logging.FileHandler(os.path.join(log_dir, "sent_tx_logs.log"), encoding="utf-8")
sent_tx_handler.setFormatter(log_formatter)
sent_tx_logger.addHandler(sent_tx_handler)





# Funkcja do logowania i wysyłania do frontendu
def log_message(message, log_type="all"):
    
    all_logger.info(message)
    if log_type == "matched":
        matched_logger.info(message)
    if log_type == "transfer_tx":
        sent_tx_logger.info(message)
    # Wysyłamy log do frontendu (wszystkie logi, niezależnie od typu)
    eel.update_logs(message,log_type)
    

