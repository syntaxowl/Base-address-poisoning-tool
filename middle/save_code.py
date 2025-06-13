import eel
import os
from  backend.token_gen.generate_tocken import save_tocken


@eel.expose
def save_code(name,full_code):
    save_tocken(name, full_code)
    