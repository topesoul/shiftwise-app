// /workspace/shiftwise/static/js/billing.js

document.addEventListener('DOMContentLoaded', function () {
    // Billing Cycle Toggle Functionality
    initBillingCycleToggle();
});

// Billing Cycle Toggle Functionality
function initBillingCycleToggle() {
    const monthlyToggle = document.getElementById('monthlyToggle');
    const yearlyToggle = document.getElementById('yearlyToggle');
    const priceValues = document.querySelectorAll('.price-value');
    const subscribeButtons = document.querySelectorAll('.subscribe-button');

    function updatePricingAndActions(isMonthly) {
        priceValues.forEach(function(span) {
            if (isMonthly) {
                const monthlyPrice = span.getAttribute('data-monthly-price');
                span.textContent = monthlyPrice ? monthlyPrice : 'N/A';
                span.nextElementSibling.textContent = monthlyPrice ? '/mo' : '/n/a';
            } else {
                const yearlyPrice = span.getAttribute('data-yearly-price');
                span.textContent = yearlyPrice ? yearlyPrice : 'N/A';
                span.nextElementSibling.textContent = yearlyPrice ? '/yr' : '/n/a';
            }
        });

        const baseUrl = "/subscriptions/subscribe/";
        subscribeButtons.forEach(function(button) {
            const planId = isMonthly ? button.getAttribute('data-monthly-plan-id') : button.getAttribute('data-yearly-plan-id');
            if (planId) {
                button.href = baseUrl + planId + "/";
                button.classList.remove('disabled');
            } else {
                button.href = "#";
                button.classList.add('disabled');
            }
        });
    }

    if (monthlyToggle && yearlyToggle) {
        monthlyToggle.addEventListener('change', function() {
            if (this.checked) updatePricingAndActions(true);
        });
        yearlyToggle.addEventListener('change', function() {
            if (this.checked) updatePricingAndActions(false);
        });
        // Initialize based on the default checked toggle
        updatePricingAndActions(monthlyToggle.checked);
    }
}
