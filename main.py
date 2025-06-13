import eel
import os

from backend.token_gen.deployp import deploy_token
from  backend.token_gen.generate_tocken import generate_token_code 
from backend.token_gen.generate_tocken import save_tocken
from backend.token_gen.verif import verify_contract_source_code
from backend.source_destinantion.filters import filter_addresses
from backend.source_destinantion.find_good_to_adresses import analyze_transactions
from backend.adres_gen.vanity import find_vanity_address
from backend.monitor.monitor import start_monitoring
from backend.monitor.monitor import start_monitor
from backend.monitor.monitor import subscribe_logs
from backend.stats.database_stats import get_stats_by_interval
from middle.gen_tocken import update_token_code
from middle.save_data import save_keys
from middle.save_code import save_code
from middle.deploy import deploy_token
from middle.verif import verif
from middle.save_data import save_contract_address

if __name__ == '__main__':
    # Absolutna ścieżka do folderu front
    front_path = os.path.join(os.path.dirname(__file__), "front")
    eel.init(front_path)
    eel.start('index.html', mode="chrome", size=(641, 628), cmdline_args=['--incognito'])

    