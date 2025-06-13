// Wybór trybu monitorowania
function mode_choose() {
    console.log("mode_choose called");
    const mode = document.getElementById('mode');
    const txtInputs = document.getElementById('txtInputs');
    const fileInputs = document.getElementById('fileInputs');

    if (!mode || !txtInputs || !fileInputs) {
        console.error("Error: One or more elements (mode, txtInputs, fileInputs) not found");
        showToast("Błąd: Brak elementów formularza", "error");
        return;
    }

    txtInputs.style.display = mode.value === 'monitor_from_vanity' ? 'block' : 'none';
    fileInputs.style.display = mode.value === 'monitor_to' || mode.value === 'monitor_from_to' ? 'block' : 'none';
}

// Wybór typu ataku
function attack_choose() {
    console.log("attack_choose called");
    const attackType = document.getElementById('attack_type'); // Poprawiono ID na 'attack_type'

    if (!attackType) {
        console.error("Error: attack_type element not found");
        showToast("Błąd: Nie wybrano typu ataku", "error");
        return;
    }
}

// Uruchamianie monitorowania
async function startMonitoring() {
    console.log("startMonitoring called");
    const attack_type = document.getElementById('attack_type');
    const mode = document.getElementById('mode');
    const txtFile = document.getElementById('txtFile');
    const csvFile = document.getElementById('csvFile');
    const logPanel = document.getElementById('log-panel');
    const toggleButton = document.getElementById('toggle-log');

    if (!mode || !txtFile || !csvFile || !logPanel || !toggleButton) {
        console.error("Error: One or more elements (mode, txtFile, csvFile, log-panel, toggle-log) not found");
        showToast("Błąd: Brak elementów interfejsu", "error");
        return;
    }

    if (!txtFile.files[0] && !csvFile.files[0]) {
        console.error("Error: No file selected");
        showToast("Błąd: Wybierz plik TXT lub CSV", "error");
        return;
    }

  

    try {
        let input_data = null;
        if (txtFile.files[0]) {
            input_data = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result);
                reader.onerror = (e) => reject(e);
                reader.readAsText(txtFile.files[0]);
            });
        } else if (csvFile.files[0]) {
            input_data = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result);
                reader.onerror = (e) => reject(e);
                reader.readAsText(csvFile.files[0]);
            });
        }

        console.log("Mode:", mode.value);
        console.log("Input data:", input_data ? "Zawartość odczytana" : "Brak pliku");

        logPanel.classList.add('open');
        logPanel.setAttribute('aria-hidden', 'false');
        toggleButton.textContent = 'Ukryj logi';
        toggleButton.setAttribute('aria-expanded', 'true');

        await eel.start_monitor(attack_type.value,mode.value, input_data)();
        showToast("Monitorowanie rozpoczęte", "success");
    } catch (error) {
        console.error("Błąd podczas uruchamiania monitorowania:", error);
        showToast(`Błąd: ${error.message}`, "error");
    } finally {
        showLoader(false);
    }
}

// Zatrzymywanie monitorowania
function stopMonitoring() {    //poprawić
    console.log("stopMonitoring called");
    eel.stop_monitor()();
    showToast("Monitorowanie zatrzymane", "success");
}

// Przełączanie panelu logów
function toggleLogPanel() {
    console.log("toggleLogPanel called");
    const logPanel = document.getElementById('log-panel');
    const toggleButton = document.getElementById('toggle-log');

    if (!logPanel || !toggleButton) {
        console.error("Error: log-panel or toggle-log not found");
        showToast("Błąd: Brak panelu logów", "error");
        return;
    }

    const isOpen = logPanel.classList.toggle('open');
    logPanel.setAttribute('aria-hidden', !isOpen);
    toggleButton.textContent = isOpen ? 'Ukryj logi' : 'Pokaż logi';
    toggleButton.setAttribute('aria-expanded', isOpen);
    if (!isOpen) {
        logPanel.style.height = '400px'; // Reset wysokości
    }
}

// Przełączanie zakładek logów
function showLogs(tab) {
    console.log("showLogs called with tab:", tab);
    const logContents = document.querySelectorAll('.log-content');
    const tabs = document.querySelectorAll('.log-tab');

    logContents.forEach(content => {
        content.classList.toggle('hidden', content.id !== `logs-${tab}`);
    });

    tabs.forEach(t => {
        const isActive = t.dataset.tab === tab;
        t.classList.toggle('active', isActive);
        t.setAttribute('aria-selected', isActive);
    });

    const selectedLog = document.getElementById(`logs-${tab}`);
    if (selectedLog) {
        selectedLog.scrollTop = selectedLog.scrollHeight; // Auto-scroll
    } else {
        console.error(`Error: logs-${tab} not found`);
        showToast(`Błąd: Brak zakładki ${tab}`, "error");
    }
}

// Aktualizacja logów
eel.expose(update_logs);
function update_logs(message, log_type) {
    console.log("update_logs called with message:", message, "log_type:", log_type);
    const allLogs = document.getElementById('logs-all');
    const matchedLogs = document.getElementById('logs-matched');
    const sentTxLogs = document.getElementById('logs-sent_tx');

    if (!allLogs || !matchedLogs || !sentTxLogs) {
        console.error("Error: One or more log elements (logs-all, logs-matched, logs-sent_tx) not found");
        showToast("Błąd: Brak elementów logów", "error");
        return;
    }

    // Dodaj do wszystkich logów
    allLogs.textContent += `${new Date().toLocaleTimeString()} | ${message}\n`;
    allLogs.scrollTop = allLogs.scrollHeight;

    // Dodaj do odpowiedniej zakładki
    if (log_type === "matched") {
        matchedLogs.textContent += `${new Date().toLocaleTimeString()} | ${message}\n`;
        matchedLogs.scrollTop = matchedLogs.scrollHeight;
    }
    if (log_type === "transfer_tx") {
        sentTxLogs.textContent += `${new Date().toLocaleTimeString()} | ${message}\n`;
        sentTxLogs.scrollTop = sentTxLogs.scrollHeight;
    }

    // Ogranicz liczbę linii (np. 1000)
    const maxLines = 1000;
    [allLogs, matchedLogs, sentTxLogs].forEach(log => {
        const lines = log.textContent.split('\n');
        if (lines.length > maxLines) {
            log.textContent = lines.slice(-maxLines).join('\n');
        }
    });
}

// Czyszczenie logów
async function clearLogs() {
    console.log("clearLogs called");
    const allLogs = document.getElementById('logs-all');
    const matchedLogs = document.getElementById('logs-matched');
    const sentTxLogs = document.getElementById('logs-sent_tx');

    if (!allLogs || !matchedLogs || !sentTxLogs) {
        console.error("Error: One or more log elements (logs-all, logs-matched, logs-sent_tx) not found");
        showToast("Błąd: Brak elementów logów", "error");
        return;
    }

    try {
        
        allLogs.textContent = '';
        matchedLogs.textContent = '';
        sentTxLogs.textContent = '';
        showToast("Logi wyczyszczone", "success");
    } catch (error) {
        console.error("Błąd podczas czyszczenia logów:", error);
        showToast(`Błąd: ${error.message}`, "error");
    }
}

// Aktualizacja etykiet plików
document.addEventListener('DOMContentLoaded', () => {
    const txtFile = document.getElementById('txtFile');
    const csvFile = document.getElementById('csvFile');

    if (txtFile) {
        txtFile.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'Wybierz plik TXT';
            document.getElementById('txtFileLabel').textContent = fileName;
            showToast(`Wczytano plik: ${fileName}`, "success");
        });
    }

    if (csvFile) {
        csvFile.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'Wybierz plik CSV';
            document.getElementById('csvFileLabel').textContent = fileName;
            showToast(`Wczytano plik: ${fileName}`, "success");
        });
    }
});

// Nowe funkcje

// Powiadomienia (toasty)
function showToast(message, type = "info") {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

function updateEventCounter(log_type) {
    if (log_type === "matched") {
        eventCounter.matched++;
    } else if (log_type === "transfer_tx") {
        eventCounter.transfer_tx++;
    }
    const counterDisplay = document.getElementById('event-counter');
    if (counterDisplay) {
        counterDisplay.textContent = `Zdarzenia: Znalezione: ${eventCounter.matched}, Wysłane: ${eventCounter.transfer_tx}`;
    }
}

// Przeciąganie panelu logów
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOMContentLoaded: Initializing drag handler");
    const logPanel = document.getElementById('log-panel');
    const handle = document.querySelector('.log-panel-handle');

    if (!logPanel || !handle) {
        console.error("Error: log-panel or log-panel-handle not found");
        showToast("Błąd: Brak panelu logów lub uchwytu", "error");
        return;
    }

    let isDragging = false;
    let startY, startHeight;

    handle.addEventListener('mousedown', (e) => {
        console.log("mousedown on log-panel-handle");
        isDragging = true;
        startY = e.clientY;
        startHeight = logPanel.getBoundingClientRect().height;
        logPanel.classList.add('open');
        e.preventDefault();
    });

    handle.addEventListener('touchstart', (e) => {
        console.log("touchstart on log-panel-handle");
        isDragging = true;
        startY = e.touches[0].clientY;
        startHeight = logPanel.getBoundingClientRect().height;
        logPanel.classList.add('open');
        e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const deltaY = startY - e.clientY;
        let newHeight = startHeight + deltaY;
        const minHeight = 100;
        const maxHeight = window.innerHeight - 50;
        newHeight = Math.max(minHeight, Math.min(newHeight, maxHeight));
        logPanel.style.height = `${newHeight}px`;
    });

    document.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        const deltaY = startY - e.touches[0].clientY;
        let newHeight = startHeight + deltaY;
        const minHeight = 100;
        const maxHeight = window.innerHeight - 50;
        newHeight = Math.max(minHeight, Math.min(newHeight, maxHeight));
        logPanel.style.height = `${newHeight}px`;
    });

    document.addEventListener('mouseup', () => {
        if (isDragging) {
            console.log("mouseup: Stopping drag");
            isDragging = false;
        }
    });

    document.addEventListener('touchend', () => {
        if (isDragging) {
            console.log("touchend: Stopping drag");
            isDragging = false;
        }
    });

    handle.addEventListener('dblclick', () => {
        console.log("dblclick on log-panel-handle");
        const currentHeight = logPanel.getBoundingClientRect().height;
        const maxHeight = window.innerHeight - 50;
        if (currentHeight >= maxHeight - 10) {
            logPanel.style.height = '400px';
        } else {
            logPanel.style.height = `${maxHeight}px`;
        }
        logPanel.classList.add('open');
    });

    // Inicjalizacja licznika zdarzeń
    const counterDisplay = document.createElement('div');
    counterDisplay.id = 'event-counter';
    counterDisplay.textContent = 'Zdarzenia: Znalezione: 0, Wysłane: 0';
    document.querySelector('.log-controls').appendChild(counterDisplay);
});