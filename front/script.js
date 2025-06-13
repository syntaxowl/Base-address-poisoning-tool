document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll(".tab-button");
    const tabContent = document.getElementById("tabContent");

    async function loadTabContent(tabId) {
        try {
            let content = `<p>Domyślna treść dla ${tabId}</p>`;

            if (tabId === "tab2") {
                const response = await fetch("token_generator/token_generator.html");
                content = await response.text();
            }
            // Ładuj zawartość dla tab2
            if (tabId === "tab1") {
                const response = await fetch("config/config.html");
                content = await response.text();
            }
            if (tabId === "tab3") {
                const response = await fetch("filters/filters.html");
                content = await response.text();
            }
            if (tabId === "tab4") {
                const response = await fetch("vanity/vanity.html");
                content = await response.text();
            }

            if (tabId === "tab5") {
                const response = await fetch("monitor/monitor.html");
                content = await response.text();
            }
            if (tabId === "tab6") {
                const response = await fetch("stats/stats.html");
                content = await response.text();
            }
            tabContent.innerHTML = content;



            if (tabId === "tab2") {

                const deployButton = document.getElementById("deploy");
                const verifButton = document.getElementById("verif");
                const save = document.getElementById("save");

                    if (save) {
                        save.addEventListener("click", saveCode);
                    } else {
                        console.error("Nie znaleziono przycisku po załadowaniu");
                    }
                    if (deployButton) {
                        deployButton.addEventListener("click", deployCode);
                    } else {
                        console.error("Nie znaleziono przycisku po załadowaniu");
                    }
                    if (verifButton) {
                        verifButton.addEventListener("click", verifCode);
                    } else {
                        console.error("Nie znaleziono przycisku po załadowaniu");
                    }
            }
          
            // Podłącz listener po załadowaniu tab0.html
            if (tabId === "tab1") {
                const saveButton = document.getElementById("save-button");
                if (saveButton) {
                    saveButton.addEventListener("click", saveKeys);
                } else {
                    console.error("Nie znaleziono przycisku po załadowaniu");
                }
            }

            if (tabId === "tab3") {
                const generateButton = document.getElementById("generate");
                const fileInput = document.getElementById("file-input");
                const prefixInput = document.getElementById("prefix");
                const suffixInput = document.getElementById("suffix");
                const lengthPrefixInput = document.getElementById("length-prefix");
                const lengthSuffixInput = document.getElementById("length-suffix");
            
                if (generateButton) {
                    generateButton.addEventListener("click", () => {
                        const prefix = prefixInput ? prefixInput.value.trim() : "";
                        const suffix = suffixInput ? suffixInput.value.trim() : "";
                        const lengthPrefix = lengthPrefixInput ? parseInt(lengthPrefixInput.value) || 0 : 0;
                        const lengthSuffix = lengthSuffixInput ? parseInt(lengthSuffixInput.value) || 0 : 0;
                        const file = fileInput ? fileInput.files[0] : null;
            
                        if (file) {
                            processFile(file, lengthPrefix, lengthSuffix);
                        } else {
                            findVanityAddress(prefix, suffix, lengthPrefix, lengthSuffix);
                        }
                    });
                } else {
                    console.error("Nie znaleziono przycisku Generate");
                }
            }
        
            if (tabId === "tab6") {
                const apexScript = document.createElement("script");
                apexScript.src = "web/apexcharts.min.js";
                apexScript.async = false;
                document.body.appendChild(apexScript);
                apexScript.onload = () => {
                    console.log("ApexCharts załadowany");
                    const statsScript = document.createElement("script");
                    statsScript.src = "stats/stats.js";
                    statsScript.async = false;
                    document.body.appendChild(statsScript);
                };
                apexScript.onerror = () => {
                    console.error("Błąd ładowania ApexCharts");
                    tabContent.innerHTML = "<p>Błąd ładowania ApexCharts. Sprawdź, czy plik lib/apexcharts.min.js istnieje.</p>";
                };
            }
            

        } catch (error) {
            tabContent.innerHTML = `<p>Błąd script.js: ${error.message}</p>`;
        }




    }


    



    buttons.forEach(button => {
        button.addEventListener("click", () => {
            buttons.forEach(btn => btn.classList.remove("active"));
            button.classList.add("active");
            const tabId = button.getAttribute("data-tab");
            loadTabContent(tabId);
        });
    });

    loadTabContent("tab1");
});