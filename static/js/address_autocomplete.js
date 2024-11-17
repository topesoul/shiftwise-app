// /workspace/shiftwise/static/js/address_autocomplete.js

function initAutocomplete() {
    // Initialize autocomplete for agency address
    const addressInput = document.getElementById('id_agency_address_line1') || document.getElementById('id_address_line1');
    
    if (addressInput) {
        const autocomplete = new google.maps.places.Autocomplete(addressInput, {
            types: ['geocode'], // Restrict results to addresses
            componentRestrictions: { country: 'uk' } // Restrict to UK addresses
        });

        autocomplete.addListener('place_changed', () => {
            const place = autocomplete.getPlace();
            if (!place.geometry) {
                console.log("No details available for input: '" + place.name + "'");
                return;
            }

            // Extract latitude and longitude
            const lat = place.geometry.location.lat();
            const lng = place.geometry.location.lng();

            // Set the hidden latitude and longitude fields
            const latField = document.getElementById('id_agency_latitude') || document.getElementById('id_latitude');
            const lngField = document.getElementById('id_agency_longitude') || document.getElementById('id_longitude');

            if (latField && lngField) {
                latField.value = lat;
                lngField.value = lng;

                console.log(`Latitude set to: ${lat}`);
                console.log(`Longitude set to: ${lng}`);
            } else {
                console.error("Hidden latitude or longitude field not found.");
            }
        });
    } else {
        console.error("Address input field not found.");
    }
}

// Ensure that initAutocomplete is accessible globally
window.initAutocomplete = initAutocomplete;
