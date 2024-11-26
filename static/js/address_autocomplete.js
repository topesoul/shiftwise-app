// static/js/address_autocomplete.js

// Ensure `initAutocomplete` is globally accessible for Google Maps API
window.initAutocomplete = function () {
    console.log("Google Maps API loaded successfully.");

    if (typeof $ === "undefined") {
        console.error("jQuery is not loaded. Ensure jQuery is included before this script.");
        return;
    }

    const $addressInputs = $("input.address-autocomplete");
    console.log(`Found ${$addressInputs.length} address-autocomplete inputs.`);

    $addressInputs.each(function () {
        const input = this;
        const inputId = $(input).attr("id");
        console.log(`Initializing autocomplete for input ID: ${inputId}`);

        const baseIdMatch = inputId.match(/^(.*)address_line1$/);
        if (!baseIdMatch) {
            console.error(`Input ID "${inputId}" does not end with 'address_line1'.`);
            return;
        }
        const baseId = baseIdMatch[1];

        const autocomplete = new google.maps.places.Autocomplete(input, {
            types: ["geocode"],
            componentRestrictions: { country: ["uk"] },
        });

        autocomplete.setFields(["address_component", "geometry"]);

        autocomplete.addListener("place_changed", function () {
            console.log(`Place changed for input ID: ${inputId}`);
            const place = autocomplete.getPlace();

            if (place.geometry && place.geometry.location) {
                console.log(`Geocoded location: ${place.geometry.location.lat()}, ${place.geometry.location.lng()}`);
                // Set fields
                const setField = (fieldId, value) => $(`#${fieldId}`).val(value);

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

                // Reset fields
                Object.keys(fieldMap).forEach((key) => setField(fieldMap[key], ""));

                place.address_components.forEach((component) => {
                    const componentType = component.types[0];
                    switch (componentType) {
                        case "street_number":
                            setField(fieldMap.address_line1, component.long_name + " ");
                            break;
                        case "route":
                            setField(fieldMap.address_line1, $(`#${fieldMap.address_line1}`).val() + component.long_name);
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

// Ensure DOM is fully loaded before initializing Google Maps Autocomplete
$(document).ready(function () {
    if (typeof google !== "undefined" && typeof google.maps !== "undefined") {
        initAutocomplete();
    } else {
        console.error("Google Maps API is not loaded.");
    }
});
