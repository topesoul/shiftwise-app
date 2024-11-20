// /workspace/shiftwise/static/js/billing.js

document.addEventListener('DOMContentLoaded', function () {
    const monthlyToggle = document.getElementById('monthlyToggle');
    const yearlyToggle = document.getElementById('yearlyToggle');
    const priceValues = document.querySelectorAll('.price-value');

    function updatePrices(billingCycle) {
        priceValues.forEach(function(priceSpan) {
            const monthlyPrice = priceSpan.getAttribute('data-monthly-price');
            const yearlyPrice = priceSpan.getAttribute('data-yearly-price');
            if (billingCycle === 'monthly' && monthlyPrice) {
                priceSpan.textContent = monthlyPrice;
                priceSpan.nextElementSibling.textContent = '/mo';
            } else if (billingCycle === 'yearly' && yearlyPrice) {
                priceSpan.textContent = yearlyPrice;
                priceSpan.nextElementSibling.textContent = '/yr';
            }
        });
    }

    monthlyToggle.addEventListener('change', function () {
        if (this.checked) {
            updatePrices('monthly');
        }
    });

    yearlyToggle.addEventListener('change', function () {
        if (this.checked) {
            updatePrices('yearly');
        }
    });

    // Initialize with monthly plans displayed
    updatePrices('monthly');
});
