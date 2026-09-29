document.addEventListener('DOMContentLoaded', function () {
    var body = document.body;
    var themeToggle = document.querySelector('.theme-toggle');
    var dropZone = document.getElementById('dropZone');
    var fileInput = document.getElementById('fileInput');
    var fileSelect = document.getElementById('fileSelect');
    var fileLabel = document.getElementById('fileLabel');
    var processingState = document.getElementById('processingState');
    var uploadForm = document.getElementById('uploadForm');

    if (themeToggle) {
        var currentTheme = localStorage.getItem('app-theme');
        if (currentTheme === 'dark') {
            body.classList.add('dark');
            themeToggle.textContent = 'Light Mode';
        }

        themeToggle.addEventListener('click', function () {
            var isDark = body.classList.toggle('dark');
            themeToggle.textContent = isDark ? 'Light Mode' : 'Dark Mode';
            localStorage.setItem('app-theme', isDark ? 'dark' : 'light');
        });
    }

    if (dropZone && fileInput && fileSelect && fileLabel) {
        var updateLabel = function () {
            fileLabel.textContent = fileInput.files.length > 0 ? fileInput.files[0].name : 'No file selected';
        };

        ['dragenter', 'dragover'].forEach(function (eventName) {
            dropZone.addEventListener(eventName, function (event) {
                event.preventDefault();
                event.stopPropagation();
                dropZone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(function (eventName) {
            dropZone.addEventListener(eventName, function (event) {
                event.preventDefault();
                event.stopPropagation();
                dropZone.classList.remove('dragover');
            });
        });

        dropZone.addEventListener('drop', function (event) {
            var files = event.dataTransfer.files;
            if (files.length) {
                fileInput.files = files;
                updateLabel();
            }
        });

        dropZone.addEventListener('click', function () { fileInput.click(); });
        fileSelect.addEventListener('click', function () { fileInput.click(); });
        fileInput.addEventListener('change', updateLabel);

        uploadForm.addEventListener('submit', function () {
            if (processingState) {
                processingState.classList.remove('hidden');
            }
            fileSelect.disabled = true;
        });
    }

    if (window.dashboardData) {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js did not load. Charts cannot be rendered.');
            return;
        }

        var charts = window.dashboardData.charts || {};
        var prediction = window.dashboardData.prediction || null;

        var chartOptions = {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                tooltip: { enabled: true, mode: 'index', intersect: false },
            },
        };

        if (charts.bar1) {
            document.getElementById('bar1_title').textContent = charts.bar1.title;
            document.getElementById('bar1_desc').textContent = charts.bar1.description;
            new Chart(document.getElementById('barChart1'), {
                type: 'bar',
                data: {
                    labels: charts.bar1.labels,
                    datasets: [{
                        label: charts.bar1.title,
                        data: charts.bar1.values,
                        backgroundColor: 'rgba(37, 99, 235, 0.7)',
                        borderRadius: 10,
                    }],
                },
                options: chartOptions,
            });
        }

        if (charts.bar2) {
            document.getElementById('bar2_title').textContent = charts.bar2.title;
            document.getElementById('bar2_desc').textContent = charts.bar2.description;
            new Chart(document.getElementById('barChart2'), {
                type: 'bar',
                data: {
                    labels: charts.bar2.labels,
                    datasets: [{
                        label: charts.bar2.title,
                        data: charts.bar2.values,
                        backgroundColor: 'rgba(14, 165, 233, 0.75)',
                        borderRadius: 10,
                    }],
                },
                options: chartOptions,
            });
        }

        if (prediction) {
            document.getElementById('pred_title').textContent = 'Future Trend Prediction (' + prediction.column + ')';
            document.getElementById('pred_desc').textContent = 'This chart uses observation index on the x-axis and shows historical values plus the forecast window for readability.';
            var actual = prediction.actual || [];
            var future = prediction.predicted || [];
            var actualPoints = actual.map(function (value, index) {
                return { x: index + 1, y: value };
            });
            var predictedPoints = future.map(function (value, index) {
                return { x: actual.length + index + 1, y: value };
            });
            var pointRadius = actual.length > 50 ? 0 : 4;
            new Chart(document.getElementById('predictionChart'), {
                type: 'line',
                data: {
                    datasets: [
                        {
                            label: 'Historic',
                            data: actualPoints,
                            borderColor: 'rgba(37, 99, 235, 0.95)',
                            backgroundColor: 'rgba(37, 99, 235, 0.15)',
                            tension: 0.2,
                            borderWidth: 2,
                            pointRadius: pointRadius,
                            fill: false,
                        },
                        {
                            label: 'Forecast',
                            data: predictedPoints,
                            borderColor: 'rgba(249, 115, 22, 0.95)',
                            backgroundColor: 'rgba(249, 115, 22, 0.18)',
                            borderDash: [6, 4],
                            tension: 0.2,
                            borderWidth: 2,
                            pointRadius: 3,
                            fill: false,
                        },
                    ],
                },
                options: Object.assign({}, chartOptions, {
                    scales: {
                        x: {
                            type: 'linear',
                            title: {
                                display: true,
                                text: 'Observation Index',
                            },
                            ticks: {
                                callback: function (value, index, ticks) {
                                    if (ticks.length <= 8) {
                                        return value;
                                    }
                                    var maxTicks = 6;
                                    var step = Math.max(1, Math.floor((ticks.length - 1) / maxTicks));
                                    if (index === 0 || index === ticks.length - 1 || index % step === 0) {
                                        return value;
                                    }
                                    return '';
                                },
                            },
                        },
                        y: {
                            title: {
                                display: true,
                                text: prediction.column,
                            },
                            ticks: {
                                maxTicksLimit: 6,
                            },
                        },
                    },
                    elements: {
                        point: {
                            radius: 0,
                        },
                        line: {
                            tension: 0.3,
                        },
                    },
                }),
            });
        } else {
            document.getElementById('pred_title').textContent = 'Prediction not available';
            document.getElementById('pred_desc').textContent = 'Not enough data for model prediction. Choose a different numeric column or upload more data.';
        }
    }
});
