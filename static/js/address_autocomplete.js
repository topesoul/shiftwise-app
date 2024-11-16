// /workspace/shiftwise/static/js/address_autocomplete.js

function initAutocomplete() {
    const addressInputs = document.querySelectorAll('.address-autocomplete');

    addressInputs.forEach(function (addressInput) {
        const autocomplete = new google.maps.places.Autocomplete(addressInput, {
            types: ['geocode'],
            componentRestrictions: { country: ['uk'] },
        });

        autocomplete.addListener('place_changed', function () {
            const place = autocomplete.getPlace();

            // Get the form fields
            const form = addressInput.form;
            const latitudeInput = form.querySelector('#id_latitude');
            const longitudeInput = form.querySelector('#id_longitude');
            const cityInput = form.querySelector('#id_city');
            const countyInput = form.querySelector('#id_county');
            const postcodeInput = form.querySelector('#id_postcode');
            const countryInput = form.querySelector('#id_country');

            // Reset fields
            if (cityInput) cityInput.value = '';
            if (countyInput) countyInput.value = '';
            if (postcodeInput) postcodeInput.value = '';
            if (countryInput) countryInput.value = '';

            // Set latitude and longitude
            if (latitudeInput) latitudeInput.value = place.geometry.location.lat();
            if (longitudeInput) longitudeInput.value = place.geometry.location.lng();

            // Parse address components
            for (const component of place.address_components) {
                const types = component.types;
                if (types.includes('locality')) {
                    if (cityInput) cityInput.value = component.long_name;
                } else if (types.includes('administrative_area_level_2')) {
                    if (countyInput) countyInput.value = component.long_name;
                } else if (types.includes('postal_code')) {
                    if (postcodeInput) postcodeInput.value = component.long_name;
                } else if (types.includes('country')) {
                    if (countryInput) countryInput.value = component.long_name;
                }
            }
        });
    });
}

// Initialize autocomplete when the page loads
document.addEventListener("DOMContentLoaded", function () {
    if (typeof google !== 'undefined') {
        initAutocomplete();
    }
});
