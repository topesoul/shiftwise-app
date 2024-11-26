// static/js/address_autocomplete.js

// static/js/address_autocomplete.js

// Ensure `initAutocomplete` is globally accessible for Google Maps API
window.initAutocomplete = function () {
    console.log("Google Maps API loaded successfully.");

    // Check for jQuery
    if (typeof $ === "undefined") {
        console.error("jQuery is not loaded. Ensure jQuery is included before this script.");
        return;
    }

    // Select all inputs with the class 'address-autocomplete'
    const $addressInputs = $("input.address-autocomplete");
    console.log(`Found ${$addressInputs.length} address-autocomplete inputs.`);

    $addressInputs.each(function () {
        const input = this;
        const inputId = $(input).attr("id");
        console.log(`Initializing autocomplete for input ID: ${inputId}`);

        // Extract base ID from the input's ID
        const baseIdMatch = inputId.match(/^(.*)address_line1$/);
        if (!baseIdMatch) {
            console.error(`Input ID "${inputId}" does not end with 'address_line1'.`);
            return;
        }
        const baseId = baseIdMatch[1];

        // Initialize Google Places Autocomplete
        const autocomplete = new google.maps.places.Autocomplete(input, {
            types: ["geocode"],
            componentRestrictions: { country: ["uk"] },
        });

        // Specify fields to retrieve from Google Places
        autocomplete.setFields(["address_component", "geometry"]);

        // Handle place selection
        autocomplete.addListener("place_changed", function () {
            console.log(`Place changed for input ID: ${inputId}`);
            const place = autocomplete.getPlace();

            if (place.geometry && place.geometry.location) {
                console.log(
                    `Geocoded location: ${place.geometry.location.lat()}, ${place.geometry.location.lng()}`
                );

                // Define mappings of field names to input IDs
                const fieldMap = {
                    address_line1: baseId + "address_line1",
                    address_line2: baseId + "address_line2",
                    city: baseId + "city",
                    county: baseId + "county",
                    postcode: baseId + "postcode",
                    country: baseId + "country",
                    latitude: baseId + "latitude",
                    longitude: baseId + "longitude",
                };

                // Helper function to set field values
                const setField = (fieldId, value) => $(`#${fieldId}`).val(value);

                // Reset all fields
                Object.keys(fieldMap).forEach((key) => setField(fieldMap[key], ""));

                // Populate fields with Google Places components
                place.address_components.forEach((component) => {
                    const componentType = component.types[0];
                    switch (componentType) {
                        case "street_number":
                            setField(fieldMap.address_line1, component.long_name + " ");
                            break;
                        case "route":
                            setField(
                                fieldMap.address_line1,
                                $(`#${fieldMap.address_line1}`).val() + component.long_name
                            );
                            break;
                        case "locality":
                            setField(fieldMap.city, component.long_name);
                            break;
                        case "administrative_area_level_2":
                            setField(fieldMap.county, component.long_name);
                            break;
                        case "postal_code":
                            setField(fieldMap.postcode, component.long_name);
                            break;
                        case "country":
                            setField(fieldMap.country, component.long_name);
                            break;
                    }
                });

                // Set latitude and longitude
                setField(fieldMap.latitude, place.geometry.location.lat());
                setField(fieldMap.longitude, place.geometry.location.lng());
            } else {
                console.error("No geometry available for selected place.");
            }
        });
    });
};

// Wait for Google Maps API and dependencies to load before initializing
function ensureDependenciesAndInitialize() {
    if (typeof google === "undefined" || typeof google.maps === "undefined") {
        console.error("Google Maps API is not loaded. Retrying...");
        setTimeout(ensureDependenciesAndInitialize, 100); // Retry after 100ms
    } else {
        initAutocomplete();
    }
}

// Run initialization when the DOM is ready
$(document).ready(function () {
    ensureDependenciesAndInitialize();
});
