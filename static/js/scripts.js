// /workspace/shiftwise/static/js/scripts.js

document.addEventListener('DOMContentLoaded', function () {
    if (window.jQuery) {

        // Billing Cycle Toggle Functionality
        initBillingCycleToggle();
    } else {
        console.error("jQuery is missing.");
    }
});

// Billing Cycle Toggle Functionality
function initBillingCycleToggle() {
    const monthlyToggle = document.getElementById('monthlyToggle');
    const yearlyToggle = document.getElementById('yearlyToggle');
    const priceValues = document.querySelectorAll('.price-value');
    const subscribeForms = document.querySelectorAll('.subscribe-form');

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

        subscribeForms.forEach(function(form) {
            const planId = isMonthly ? form.getAttribute('data-monthly-plan-id') : form.getAttribute('data-yearly-plan-id');
            if (planId) {
                form.action = "/subscriptions/subscribe/" + planId + "/";
                form.querySelector('button').disabled = false;
            } else {
                form.action = "#";
                form.querySelector('button').disabled = true;
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
