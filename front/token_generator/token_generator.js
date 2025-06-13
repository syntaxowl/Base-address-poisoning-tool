let contractAddress = null;


async function updateCode() {
    const name = document.getElementById("name").value;
    const symbol = document.getElementById("symbol").value;
    const initialSupply = document.getElementById("initialSupply").value;
    const mintable = document.getElementById("mintable").checked;
    const burnable = document.getElementById("burnable").checked;
    const pausable = document.getElementById("pausable").checked;

    const code = await eel.update_token_code(name, symbol, initialSupply, mintable, burnable, pausable)();

    const codeBlock = document.getElementById("codeOutput");
    codeBlock.textContent = code;
    Prism.highlightElement(codeBlock); // <- Kolorowanie
}


async function deployCode() {
    const name = (document.getElementById("name")?.value || "USDT") ;
    try {
        console.log(`Rozpoczynanie deploymentu tokena: ${name}`);
        const result = await eel.deploy(name)();  // Wywołujemy eel.deploy, nie deploy_token

        if (result.status === "success") {
            console.log("Deployment zakończony sukcesem:");
            console.log("Adres kontraktu:", result.address);
            document.getElementById("address").value = result.address
            console.log("Pełny wynik:", result);
            document.getElementById("codeOutput").value += `\n\n${result.message}`;
            eel.save_contract_address(result.address)()
            contractAddress= result.address
        } else {
            console.error("Błąd deploymentu:", result.message);
            console.error("Krok błędu:", result.step);
        }
    } catch (error) {
        console.error("Błąd deploy w JavaScript:", error);
    }
}


async function saveCode() {
    const name = document.getElementById("name")?.value || "USDT";
    const code = document.getElementById("codeOutput").textContent || "";
    try {
        const result = await eel.save_code(name, code)();
       // save_code(name, code)();
        console.log(result);
    } catch (error) {
        console.error("Błąd zapisu:", error);
    }
}

async function verifCode() {
    console.log("start verif")
    const contract_name = document.getElementById("name")?.value || "USDT";
    const main_file = contract_name + ".sol";
    const tmp_addr = contractAddress;

    if (!tmp_addr) {
        console.error("Brak adresu kontraktu. Najpierw wykonaj deploy!");
        return;
    }

    try {
        const result = await eel.verif(tmp_addr, main_file, contract_name)();
        console.log("Wynik weryfikacji:", result);
    
        const [status, value] = result;  // Rozpakowanie tablicy
    
        if (status === "success") {
            const guid = value;  // value to guid przy sukcesie
            console.log("GUID:", guid);
            console.log("Czekam 60 sekund...");
            await new Promise(resolve => setTimeout(resolve, 60000)); // 30 sekund
            const verif_status = await eel.check_verif_status(guid)();
            console.log("Status weryfikacji:", verif_status.status);
            
            alert(verif_status.result);
            
            
            console.log("Wynik:", verif_status.result);
        } else {
            const message = value;  // value to message przy błędzie
            console.log("Błąd weryfikacji:", message);
        }
    } catch (error) {
        console.error("Błąd weryfikacji:", error);
    }
}

/*
window.updateCode = updateCode;
window.saveCode= saveCode;
window.deployCode = deployCode;
*/
// Wywołaj raz na starcie



document.addEventListener("DOMContentLoaded", updateCode);