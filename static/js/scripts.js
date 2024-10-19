document.addEventListener('DOMContentLoaded', function() {
    const postcodeInput = document.getElementById('postcode');

    if (postcodeInput) {
        postcodeInput.addEventListener('change', function() {
            const postcode = postcodeInput.value.trim();
            if (postcode === "") {
                console.warn('Postcode field is empty.');
                // Clear address fields
                document.getElementById('address_line1').value = '';
                document.getElementById('city').value = '';
                document.getElementById('state').value = '';
                document.getElementById('country').value = '';
                document.getElementById('latitude').value = '';
                document.getElementById('longitude').value = '';
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
                    document.getElementById('address_line1').value = data.address.address_line1 || '';
                    document.getElementById('city').value = data.address.city || '';
                    document.getElementById('state').value = data.address.state || '';
                    document.getElementById('country').value = data.address.country || '';
                    document.getElementById('latitude').value = data.address.latitude || '';
                    document.getElementById('longitude').value = data.address.longitude || '';
                } else {
                    alert('Unable to fetch address details. Please check the postcode and try again.');
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
