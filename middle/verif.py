import eel
from backend.token_gen.verif import verify_contract_source_code
from backend.token_gen.verif import check_verification_status

@eel.expose
def verif(contract_address, main_file, contract_name):
    result = verify_contract_source_code(contract_address, main_file, contract_name)
    status=result["status"]
    if result["status"] == "success":
        
        message= result["message"]
        guid= result["guid"]
        return status, guid
    else:
        return status, result["message"]
    
@eel.expose
def check_verif_status(guid):
    result = check_verification_status(guid)
    return result