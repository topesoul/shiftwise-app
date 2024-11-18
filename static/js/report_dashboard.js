// /workspace/shiftwise/static/js/report_dashboard.js

document.addEventListener('DOMContentLoaded', function () {
    // Shift Chart
    const shiftsCtx = document.getElementById('shiftsChart').getContext('2d');
    const shiftsChart = new Chart(shiftsCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '# of Shifts',
                data: shiftData,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1,
                borderRadius: 5,
                maxBarThickness: 50,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                    },
                    title: {
                        display: true,
                        text: 'Number of Shifts',
                    },
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date',
                    },
                },
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                    },
                    onClick: function(e, legendItem, legend) {
                        const index = legendItem.datasetIndex;
                        const ci = legend.chart;
                        const meta = ci.getDatasetMeta(index);

                        // Toggle the visibility
                        meta.hidden = meta.hidden === null ? !ci.data.datasets[index].hidden : null;
                        ci.update();
                    },
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.y || 0;
                            return label;
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuad',
                },
            },
        }
    });

    // Performance Chart
    const performanceCtx = document.getElementById('performanceChart').getContext('2d');
    const performanceChart = new Chart(performanceCtx, {
        type: 'doughnut',
        data: {
            labels: ['Average Wellness Score', 'Average Performance Rating'],
            datasets: [{
                data: [avgWellness, avgRating],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(255, 206, 86, 0.6)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 206, 86, 1)'
                ],
                borderWidth: 1,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    enabled: true,
                },
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                    },
                    onClick: function(e, legendItem, legend) {
                        const index = legendItem.index;
                        const ci = legend.chart;
                        const meta = ci.getDatasetMeta(0);

                        // Toggle the visibility
                        meta.data[index].hidden = !meta.data[index].hidden;
                        ci.update();
                    },
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuad',
                },
            },
        }
    });
});
