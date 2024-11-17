// /workspace/shiftwise/static/js/address_autocomplete.js

function initAutocomplete() {
    // Select all input fields with the 'address-autocomplete' class
    const addressInputs = document.querySelectorAll('input.address-autocomplete');
    addressInputs.forEach(input => {
        if (input) {
            // Determine the base ID by removing 'address_line1' from the input's ID
            const baseIdMatch = input.id.match(/^(.*)address_line1$/);
            if (!baseIdMatch) {
                console.error(`Input ID "${input.id}" does not end with 'address_line1'.`);
                return;
            }
            const baseId = baseIdMatch[1];  // e.g., 'id_shift_' or 'id_profile_'

            // Initialize Google Places Autocomplete
            const autocomplete = new google.maps.places.Autocomplete(input, {
                types: ['geocode'], // Restrict results to addresses
                componentRestrictions: { country: ['uk'] } // Restrict to UK addresses
            });

            // Add listener for place selection
            autocomplete.addListener('place_changed', () => {
                const place = autocomplete.getPlace();
                if (place.geometry && place.geometry.location) {
                    // Construct IDs for latitude and longitude fields
                    const latFieldId = baseId + 'latitude';
                    const lngFieldId = baseId + 'longitude';
                    const latField = document.getElementById(latFieldId);
                    const lngField = document.getElementById(lngFieldId);

                    if (latField && lngField) {
                        latField.value = place.geometry.location.lat();
                        lngField.value = place.geometry.location.lng();

                        console.log(`Latitude set to: ${latField.value}`);
                        console.log(`Longitude set to: ${lngField.value}`);
                    } else {
                        console.error(`Latitude or Longitude field not found for base ID: "${baseId}". Expected IDs: "${latFieldId}" and "${lngFieldId}".`);
                    }
                } else {
                    console.log(`No geometry available for input: '${place.name}'`);
                }
            });
        }
    });
}

// Expose the function globally to ensure it's accessible by the Google Maps API callback
window.initAutocomplete = initAutocomplete;
