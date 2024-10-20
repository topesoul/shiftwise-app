// static/js/scripts.js

document.addEventListener('DOMContentLoaded', function() {
    const postcodeInput = document.getElementById('id_postcode');

    if (postcodeInput) {
        postcodeInput.addEventListener('change', function() {
            const postcode = postcodeInput.value.trim();
            if (postcode === "") {
                console.warn('Postcode field is empty.');
                // Clear address fields
                ['id_address_line1', 'id_city', 'id_state', 'id_country', 'id_latitude', 'id_longitude'].forEach(id => {
                    const field = document.getElementById(id);
                    if (field) field.value = '';
                });
                return;
            }

            // Show loading spinner
            const spinner = document.getElementById('loadingSpinner');
            if (spinner) {
                spinner.style.display = 'inline-block';
            }

            // AJAX call to fetch address details
            fetch(`/shifts/get_address/?postcode=${encodeURIComponent(postcode)}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(response => {
                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error('Address not found for the provided postcode.');
                    } else if (response.status === 403) {
                        throw new Error('You do not have permission to perform this action.');
                    } else {
                        throw new Error('Network response was not ok.');
                    }
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Populate address fields
                    const address = data.address;
                    document.getElementById('id_address_line1').value = address.address_line1 || '';
                    document.getElementById('id_city').value = address.city || '';
                    document.getElementById('id_state').value = address.state || '';
                    document.getElementById('id_country').value = address.country || '';
                    document.getElementById('id_latitude').value = address.latitude || '';
                    document.getElementById('id_longitude').value = address.longitude || '';
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error fetching address:', error);
                alert(error.message);
            })
            .finally(() => {
                // Hide loading spinner
                if (spinner) {
                    spinner.style.display = 'none';
                }
            });
        });
    } else {
        console.warn('Postcode input field not found.');
    }
});