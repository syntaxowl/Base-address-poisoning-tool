/*
async function saveKeys() {
    const kluczApi = document.getElementById("klucz-api")?.value.trim();
    const kluczPrywatny = document.getElementById("klucz-prywatny")?.value.trim();
    const baseKey = document.getElementById("base-key")?.value.trim();
    const infura = document.getElementById("infura")?.value.trim();

    // Tworzymy obiekt tylko z niepustymi danymi
    const daneDoZapisania = {};

    if (kluczApi) daneDoZapisania.kluczApi = kluczApi;
    if (kluczPrywatny) daneDoZapisania.kluczPrywatny = kluczPrywatny;
    if (baseKey) daneDoZapisania.baseKey = baseKey;
    if (infura) daneDoZapisania.infura = infura;

    if (Object.keys(daneDoZapisania).length === 0) {
        console.log("Brak danych do zapisania.");
        return;
    }

    try {
        const wynik = await eel.save_keys(daneDoZapisania)();
        console.log(wynik);
    } catch (error) {
        console.error("Błąd Eel:", error);
    }
}
*/


async function saveKeys() {
    const kluczApi = document.getElementById("klucz-api")?.value.trim();
    const kluczPrywatny = document.getElementById("klucz-prywatny")?.value.trim();
    const baseKey = document.getElementById("base-key")?.value.trim();
    const infura = document.getElementById("infura")?.value.trim();

    const daneDoZapisania = {};
    if (kluczApi) daneDoZapisania.kluczApi = kluczApi;
    if (kluczPrywatny) daneDoZapisania.kluczPrywatny = kluczPrywatny;
    if (baseKey) daneDoZapisania.baseKey = baseKey;
    if (infura) daneDoZapisania.infura = infura;

    if (Object.keys(daneDoZapisania).length === 0) {
        console.log("Brak danych do zapisania.");
        return;
    }

    const button = document.getElementById("save-button");
    const originalText = button.textContent;
    const originalColor = button.style.backgroundColor;

    try {
        const wynik = await eel.save_keys(daneDoZapisania)();
        console.log(wynik);

        // Zmień wygląd przycisku na chwilę
        button.textContent = "✔ Zapisano!";
        button.style.backgroundColor = "#28a745"; // zielony

        setTimeout(() => {
            button.textContent = originalText;
            button.style.backgroundColor = originalColor;
        }, 2000);
        
    } catch (error) {
        console.error("Błąd Eel:", error);
        button.textContent = "❌ Błąd!";
        button.style.backgroundColor = "#dc3545"; // czerwony

        setTimeout(() => {
            button.textContent = originalText;
            button.style.backgroundColor = originalColor;
        }, 2000);
    }
}
