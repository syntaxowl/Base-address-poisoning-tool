console.log("stats.js załadowany");

// Sprawdzenie czy ApexCharts jest załadowany
if (typeof ApexCharts === 'undefined') {
    console.error("ApexCharts nie jest załadowany");
    const chartContainer = document.getElementById('chartContainer');
    if (chartContainer) {
        chartContainer.innerHTML = "<p style='color:red;padding:20px'>Błąd: Biblioteka wykresów nie została załadowana</p>";
    }
} else {
    console.log("ApexCharts załadowany poprawnie");

    // Funkcja konwersji daty do formatu lokalnego
    function toLocalISOString(date) {
        const offset = date.getTimezoneOffset();
        const adjustedDate = new Date(date.getTime() - (offset * 60 * 1000));
        return adjustedDate.toISOString().slice(0, 16) + 'Z';
    }

    // Funkcja do ustawiania okresu
    function setPeriod() {
        const period = document.getElementById('period').value;
        const now = new Date();
        let after, before;
    
        // Pokaż/ukryj kontrolki daty
        const dateControls = document.querySelectorAll('.date-control');
        dateControls.forEach(control => {
            control.style.display = period === 'custom' ? 'block' : 'none';
        });
    
        // Obliczanie dat w zależności od wybranego okresu
        if (period === 'day') {
            // Dzisiejszy dzień
            after = new Date(now);
            after.setHours(0, 0, 0, 0);
            before = new Date(now);
            before.setHours(23, 59, 59, 999);
        } else if (period === 'week') {
            // Ostatnie 7 dni
            before = new Date(now);
            before.setHours(23, 59, 59, 999);
            after = new Date(now);
            after.setDate(after.getDate() - 6);
            after.setHours(0, 0, 0, 0);
        } else if (period === 'month') {
            // Ostatnie 30 dni
            before = new Date(now);
            before.setHours(23, 59, 59, 999);
            after = new Date(now);
            after.setDate(after.getDate() - 29);
            after.setHours(0, 0, 0, 0);
        } else if (period === 'threeMonths') {
            // Ostatnie 90 dni
            before = new Date(now);
            before.setHours(23, 59, 59, 999);
            after = new Date(now);
            after.setDate(after.getDate() - 89);
            after.setHours(0, 0, 0, 0);
        } else if (period === 'custom') {
            after = document.getElementById('after').value;
            before = document.getElementById('before').value;
            return { after, before };
        }
    
        return {
            after: toLocalISOString(after),
            before: toLocalISOString(before)
        };
    }
    
    // Funkcja renderująca wykres
    async function renderChart() {
        console.log("Renderowanie wykresu...");
        try {
            let { after, before } = setPeriod();
            const interval = document.getElementById('interval').value;

            console.log(`Pobieranie danych: ${after} - ${before}, interwał: ${interval}`);
                
            // Pobieranie danych przez Eel
            const statsJson = await eel.get_stats_by_interval(after, before, interval)();
            const stats = JSON.parse(statsJson);
            console.log("Otrzymane dane:", stats);
            
            if (stats.error) {
                throw new Error(stats.error);
            }

            const chartElement = document.getElementById('logsChart');
            if (!stats || !stats.length) {
                if (chartElement) {
                    chartElement.innerHTML = "<p style='text-align:center;padding:20px'>Brak danych dla wybranego zakresu</p>";
                }
                return;
            }

            // Przygotowanie danych
            const labels = stats.map(item => item.period);
            const filtered_counts = [];
            const sended_counts = [];
            const filtered_raw = [];
            const sended_raw = [];

            stats.forEach(item => {
                filtered_all = item.filtered || 0;
                const sended = item.sended || 0;
                const filtered =filtered_all-sended
                const total =  filtered_all;
            
                
                filtered_raw.push(filtered);
                sended_raw.push(sended);
            
                
                filtered_counts.push(total ? (filtered / total) * 100 : 0);
                sended_counts.push(total ? (sended / total) * 100 : 0);
            });

            // Konfiguracja wykresu
            const options = {
                series: [
                    
                    { name: 'Filtered', data: filtered_counts },
                    { name: 'Sended', data: sended_counts }
                ],
                chart: {
                    type: 'bar',
                    height: '100%',
                    stacked: true,
                    stackType: '100%',
                    toolbar: { show: true },
                    animations: { enabled: true }
                },
                colors: ['#FF6384', '#36A2EB', '#FFCE56'],
                plotOptions: {
                    bar: {
                        horizontal: false,
                        endingShape: 'rounded',
                        columnWidth: '80%'
                    }
                },
                dataLabels: {
                    enabled: false
                },
                xaxis: {
                    categories: labels,
                    labels: {
                        rotate: -45,
                        style: {
                            fontSize: '12px'
                        }
                    }
                },
                yaxis: {
                    title: { text: 'Procentowy udział' },
                    labels: {
                        formatter: function(val) {
                            return val.toFixed(0) + '%';
                        }
                    },
                    min: 0,
                    max: 100
                },
                tooltip: {
                    y: {
                        formatter: function(val, opts) {
                            const i = opts.dataPointIndex;
                            const rawVal = opts.seriesIndex === 0 ? contract_raw[i] :
                                        opts.seriesIndex === 1 ? filtered_raw[i] :
                                        sended_raw[i];
                            return `${rawVal} (${val.toFixed(1)}%)`;
                        }
                    }
                },
                legend: {
                    position: 'top'
                }
            };

            // Usunięcie poprzedniego wykresu jeśli istnieje
            if (window.logsChart && typeof window.logsChart.destroy === 'function') {
                window.logsChart.destroy();
            }

            // Utworzenie nowego wykresu
            if (chartElement) {
                window.logsChart = new ApexCharts(chartElement, options);
                window.logsChart.render();
            }

        } catch (error) {
            console.error('Błąd renderowania wykresu:', error);
            const chartElement = document.getElementById('logsChart');
            if (chartElement) {
                chartElement.innerHTML = `<p style='color:red;padding:20px'>Błąd: ${error.message}</p>`;
            }
        }
    }

    // Make renderChart available globally
    window.renderChart = renderChart;

    // Inicjalizacja po załadowaniu DOM
    document.addEventListener('DOMContentLoaded', function() {
        const periodSelect = document.getElementById('period');
        const intervalSelect = document.getElementById('interval');
        const refreshButton = document.getElementById('refreshChart');
        
        if (periodSelect && intervalSelect && refreshButton) {
            periodSelect.addEventListener('change', function() {
                setPeriod();
                renderChart();
            });
            
            intervalSelect.addEventListener('change', renderChart);
            
            refreshButton.addEventListener('click', function(e) {
                e.preventDefault();
                renderChart();
            });
            
            // Ustawienie domyślnych wartości i pierwsze renderowanie
            periodSelect.value = 'day';
            intervalSelect.value = 'hour';
            renderChart();
        } else {
            console.error("Nie znaleziono wymaganych elementów DOM");
        }
    });
}