// /workspace/shiftwise/static/js/scripts.js

document.addEventListener('DOMContentLoaded', function () {
    if (window.jQuery) {
        // Plugins Initialization
        initBootstrapTooltips();
        initCustomSelect();
        initTimepicker();
        initDatepicker();

        // Billing Cycle Toggle Functionality
        initBillingCycleToggle();

        // Notifications Setup
        initNotifications();
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
        // Initialize based on the default checked toggle
        updatePricingAndActions(monthlyToggle.checked);
    } else {
        console.warn("Billing cycle toggle elements are missing.");
    }
}

// Notifications Setup using WebSockets
function initNotifications() {
    const userId = document.documentElement.getAttribute('data-user-id');
    const notificationContainer = document.getElementById('notification-container');

    if (userId && userId !== "0") {
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const socketUrl = protocol + window.location.host + '/ws/notifications/';
        const socket = new WebSocket(socketUrl);

        socket.onmessage = function (e) {
            const data = JSON.parse(e.data);
            const message = data.message;
            const icon = data.icon || 'fas fa-info-circle';
            const url = data.url || '#';

            const notification = document.createElement('div');
            notification.classList.add('notification', 'alert', 'alert-info', 'alert-dismissible', 'fade', 'show');
            notification.innerHTML = `
                <i class="${icon}"></i> ${message}
                ${url !== '#' ? `<a href="${url}" class="alert-link">View</a>` : ''}
                <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            `;
            notificationContainer.appendChild(notification);

            // auto-dismiss the notification after a few seconds
            setTimeout(() => {
                $(notification).alert('close');
            }, 5000);
        };

        socket.onerror = function (error) {
            console.error('WebSocket Error:', error);
        };

        socket.onclose = function (e) {
            console.error('Notification socket closed unexpectedly:', e);
            // attempt to reconnect after some time
        };
    } else {
        console.warn("User is not authenticated. Notifications will not be initialized.");
    }
}
