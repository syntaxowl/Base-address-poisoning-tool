async function runFilter() {
    const fromZero = document.getElementById('fromZero').checked;
    const inputFile = document.getElementById('inputFile').value;
    const outputFile = document.getElementById('outputFile').value;
    const minAmount = document.getElementById('minAmount').value;
    const minTransactions = document.getElementById('minTransactions').value;
    const lastDays = document.getElementById('lastDays').value;

    const result = await eel.filter_addresses(fromZero, inputFile, outputFile, minAmount, minTransactions, lastDays)();
    document.getElementById('filterResult').innerText = result;  // "Filtrowanie rozpoczęte w tle..."
}

async function runAnalysis() {
    const inputFile = document.getElementById('txInputFile').value;
    const outputCsv = document.getElementById('txOutputCsv').value;
    const minTransactions = document.getElementById('txMinTransactions').value;
    const minAmountSended = document.getElementById('txMinAmountSended').value;

    const result = await eel.analyze_transactions(inputFile, outputCsv, minTransactions, minAmountSended)();
    document.getElementById('analysisResult').innerText = result;  // "Analiza rozpoczęta w tle..."
}

// Funkcje aktualizujące wyniki z Pythona
eel.expose(update_filter_result);
function update_filter_result(message) {
    document.getElementById('filterResult').innerText = message;
}

eel.expose(update_analysis_result);
function update_analysis_result(message) {
    document.getElementById('analysisResult').innerText = message;
}