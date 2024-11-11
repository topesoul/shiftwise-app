// /workspace/shiftwise/static/js/scripts.js

/**
 * Main JavaScript File
 * Handles plugin initializations, billing cycle toggles, dark mode preferences,
 * and notifications using WebSockets.
 */

document.addEventListener('DOMContentLoaded', function () {
    if (window.jQuery) {
        // Plugins Initialization
        initBootstrapTooltips();
        initCustomSelect();
        initTimepicker();
        initSignaturePad();
        initDatepicker();

        // Billing Cycle Toggle Functionality
        initBillingCycleToggle();

        // Dark Mode Preference
        checkThemePreference();
    } else {
        console.error("jQuery is missing.");
    }
});

// Plugin Initialization Functions
function initBootstrapTooltips() {
    if (jQuery.fn.tooltip) {
        $('[data-toggle="tooltip"]').tooltip();
    } else {
        console.error("Bootstrap tooltips are not loaded.");
    }
}

function initCustomSelect() {
    if (jQuery.fn.selectize) {
        $('.custom-select').selectize({
            create: true,
            sortField: 'text'
        });
    } else {
        console.error("Selectize plugin is not loaded.");
    }
}

function initTimepicker() {
    if (jQuery.fn.timepicker) {
        $('.timepicker').timepicker({
            minuteStep: 15,
            showMeridian: false
        });
    } else {
        console.error("Timepicker plugin is not loaded.");
    }
}

function initSignaturePad() {
    // Initialize signature pad if the element is available
    const signatureCanvas = document.querySelector('.signature-pad');
    if (signatureCanvas) {
        const signaturePad = new SignaturePad(signatureCanvas, {
            penColor: '#000',
            backgroundColor: '#fff'
        });

        const clearButton = document.querySelector('.clearSignature');
        const signatureInput = document.querySelector('.signatureInput');

        if (clearButton) {
            clearButton.addEventListener('click', function () {
                signaturePad.clear();
                if (signatureInput) {
                    signatureInput.value = '';
                }
            });
        }
    } else {
        console.warn("Signature Pad element not found.");
    }
}

function initDatepicker() {
    if (jQuery.fn.datepicker) {
        $('.datepicker').datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            todayHighlight: true
        });
    } else {
        console.error("Datepicker plugin is not loaded.");
    }
}

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
        updatePricingAndActions(monthlyToggle.checked);
    } else {
        console.warn("Billing cycle toggle elements are missing.");
    }
}

// Dark Mode Functionality
function checkThemePreference() {
    const theme = localStorage.getItem('theme');
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function (e) {
            e.preventDefault();
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
        });
    }
});

// Notifications using WebSockets
document.addEventListener('DOMContentLoaded', function() {
    const notificationContainer = document.getElementById('notification-container');
    const userId = "{{ request.user.id }}";

    if (userId) {
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const socket = new WebSocket(protocol + window.location.host + '/ws/notifications/');

        socket.onmessage = function (e) {
            const data = JSON.parse(e.data);
            const message = data.message;
            const icon = data.icon;
            const url = data.url;

            const notification = document.createElement('div');
            notification.classList.add('notification', 'alert', 'alert-info', 'alert-dismissible', 'fade', 'show');
            notification.innerHTML = `
                <i class="${icon}"></i> ${message}
                ${url ? `<a href="${url}" class="alert-link">View</a>` : ''}
                <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            `;
            notificationContainer.appendChild(notification);
        };

        socket.onclose = function (e) {
            console.error('Notification socket closed unexpectedly');
        };
    }
});
