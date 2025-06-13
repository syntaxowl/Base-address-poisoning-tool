function toggleInputs() {
    const mode = document.getElementById("mode").value;
    document.getElementById("manualInputs").style.display = mode === "manual" ? "block" : "none";
    document.getElementById("addressInputs").style.display = mode === "address" ? "block" : "none";
    document.getElementById("fileInputs").style.display = mode === "file" ? "block" : "none";
}

function startGeneration() {
    let mode = document.getElementById("mode").value;
    let input_data = "";
    let prefix = "";
    let suffix = "";
    let prefix_length = 0;
    let suffix_length = 0;

    if (mode === "manual") {
        prefix = document.getElementById("prefix").value;
        suffix = document.getElementById("suffix").value;
    } else if (mode === "address") {
        input_data = document.getElementById("address").value;
        prefix_length = document.getElementById("prefix_length").value || 0;
        suffix_length = document.getElementById("suffix_length").value || 0;
    } else if (mode === "file") {
        let file = document.getElementById("file").files[0];
        if (!file) {
            alert("Wybierz plik!");
            return;
        }
        prefix_length = document.getElementById("file_prefix_length").value || 0;
        suffix_length = document.getElementById("file_suffix_length").value || 0;
        const fileLabel = document.getElementById("file-label");
        if (fileLabel) {
            fileLabel.innerText = `Załadowano: ${file.name}`;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            input_data = e.target.result;
            document.getElementById("status").innerText = "Rozpoczęcie generowania...";
            document.getElementById("stats-container").innerText = "Oczekiwanie na statystyki...";
            eel.find_vanity_address(mode, input_data, prefix_length, suffix_length, prefix, suffix)(handleResult);
        };
        reader.readAsText(file);
        return;
    }

    document.getElementById("status").innerText = "Rozpoczęcie generowania...";
    document.getElementById("stats-container").innerText = "Oczekiwanie na statystyki...";
    eel.find_vanity_address(mode, input_data, prefix_length, suffix_length, prefix, suffix)(handleResult);
}

function handleResult(result) {
    if (!result) {
        document.getElementById("result").innerText = "Błąd: Brak odpowiedzi z serwera";
        document.getElementById("status").innerText = "";
        document.getElementById("stats-container").innerText = "";
        return;
    }

    if (result.success) {
        let resultHTML = "";
        if (document.getElementById("mode").value === "file") {
            resultHTML += `<a href="vanity_eth_results.csv" download>Pobierz wyniki CSV</a>`;
        }

        resultHTML += '<h2>Wyniki generowania:</h2><table border="1">';
        resultHTML += '<tr><th>Adres wejściowy</th><th>Adres wygenerowany</th><th>Klucz prywatny</th><th>Próby</th><th>Prędkość</th><th>Czas</th></tr>';

        result.results.forEach(item => {
            resultHTML += `
                <tr>
                    <td>${item.input_address || "N/A"}</td>
                    <td>${item.address}</td>
                    <td>${item.private_key}</td>
                    <td>${item.attempts}</td>
                    <td>${item.speed} addr/s</td>
                    <td>${item.time.toFixed(2)} sek</td>
                </tr>
            `;
        });
        resultHTML += '</table>';

        document.getElementById("result").innerHTML = resultHTML;
        document.getElementById("stats-container").innerText = "Generowanie zakończone.";
    } else {
        document.getElementById("result").innerText = result.error;
        document.getElementById("stats-container").innerText = "";
    }

    document.getElementById("status").innerText = "";
}


eel.expose(update_status);  // Zmieniono z updateStatus na update_status
function update_status(status_text) {
    //console.log("Otrzymano status:", status_text);  // Debugowanie
    const statsContainer = document.getElementById("stats-container");
    if (statsContainer) {
        statsContainer.innerText = status_text;  // Wyświetlanie statystyk w kontenerze
    }
}

function stopGeneration() {
    console.log("nacisnieto przycisk")
    eel.stop_generation()(function(result) {
        document.getElementById("stats-container").innerText = "Generowanie zatrzymane.";
        document.getElementById("status").innerText = "";
        document.getElementById("stop_button").disabled = true;
        if (result.success) {
            document.getElementById("result").innerText = result.success;
        }
    });
}


document.addEventListener("DOMContentLoaded", toggleInputs);