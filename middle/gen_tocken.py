import eel
from backend.token_gen.generate_tocken import generate_token_code

@eel.expose
def update_token_code(name, symbol, initial_supply, mintable, burnable, pausable):
    try:
        initial_supply = int(initial_supply)  # Konwersja stringa z JS na int
        code = generate_token_code(name, symbol, initial_supply, mintable, burnable, pausable)
        return code
    except ValueError:
        return "Błąd: Początkowa podaż musi być liczbą!"
    except Exception as e:
        return f"Błąd: {str(e)}"