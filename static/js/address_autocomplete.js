// /workspace/shiftwise/static/js/address_autocomplete.js

/**
 * Initialize Address Autocomplete using Google Places API
 * This function is called as a callback from the Google Maps API script.
 */

function initAutocomplete() {
    // Initialize Address Autocomplete for all elements with the 'address-autocomplete' class
    const addressInputs = document.querySelectorAll('.address-autocomplete');

    addressInputs.forEach(input => {
        const autocomplete = new google.maps.places.Autocomplete(input, {
            types: ['address'],
            componentRestrictions: { country: 'uk' },  // Adjust based on your target country
        });

        autocomplete.addListener('place_changed', function () {
            const place = autocomplete.getPlace();

            if (!place.geometry) {
                // User entered the name of a Place that was not suggested and pressed the Enter key
                alert("No details available for input: '" + place.name + "'");
                return;
            }

            // Extract address components
            const addressComponents = place.address_components;
            const components = {};

            addressComponents.forEach(component => {
                const types = component.types;
                if (types.includes('street_number')) {
                    components['street_number'] = component.long_name;
                }
                if (types.includes('route')) {
                    components['route'] = component.long_name;
                }
                if (types.includes('locality') || types.includes('postal_town')) {
                    components['city'] = component.long_name;
                }
                if (types.includes('administrative_area_level_2')) {
                    components['county'] = component.long_name;
                }
                if (types.includes('postal_code')) {
                    components['postcode'] = component.long_name;
                }
                if (types.includes('country')) {
                    components['country'] = component.long_name;
                }
            });

            // Combine street number and route for address_line1
            const address_line1 = `${components.street_number || ''} ${components.route || ''}`.trim();
            input.value = address_line1;

            // Find the closest form to populate other fields
            const form = input.closest('form');
            if (form) {
                // Populate address_line1 (already set)
                // Populate address_line2 (if needed, based on your requirements)
                const addressLine2Input = form.querySelector('#id_address_line2');
                if (addressLine2Input) {
                    addressLine2Input.value = '';  // Reset or populate as needed
                }

                // Populate city
                const cityInput = form.querySelector('#id_city');
                if (cityInput) {
                    cityInput.value = components.city || '';
                }

                // Populate county
                const countyInput = form.querySelector('#id_county');
                if (countyInput) {
                    countyInput.value = components.county || '';
                }

                // Populate postcode
                const postcodeInput = form.querySelector('#id_postcode');
                if (postcodeInput) {
                    postcodeInput.value = components.postcode || '';
                }

                // Populate country
                const countryInput = form.querySelector('#id_country');
                if (countryInput) {
                    countryInput.value = components.country || '';
                }

                // Populate latitude and longitude
                const latitudeInput = form.querySelector('#id_latitude');
                const longitudeInput = form.querySelector('#id_longitude');
                if (latitudeInput && longitudeInput) {
                    latitudeInput.value = place.geometry.location.lat();
                    longitudeInput.value = place.geometry.location.lng();
                }
            }
        });
    });
}

// Ensure the function is globally accessible
window.initAutocomplete = initAutocomplete;