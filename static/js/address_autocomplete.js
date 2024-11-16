// static/js/address_autocomplete.js

function initAutocomplete() {
    const addressInput = document.getElementById('id_address_line1');
    const autocomplete = new google.maps.places.Autocomplete(addressInput, {
        types: ['geocode'],
    });

    autocomplete.addListener('place_changed', function () {
        const place = autocomplete.getPlace();
        if (!place.geometry) {
            // User entered the name of a Place that was not suggested and pressed the Enter key
            window.alert("No details available for input: '" + place.name + "'");
            return;
        }

        // Extract latitude and longitude
        const latitude = place.geometry.location.lat();
        const longitude = place.geometry.location.lng();

        // Set the hidden fields
        document.getElementById('id_latitude').value = latitude;
        document.getElementById('id_longitude').value = longitude;

        // Extract address components
        const addressComponents = place.address_components;
        const componentForm = {
            street_number: 'short_name',
            route: 'long_name',
            locality: 'long_name',
            administrative_area_level_1: 'short_name',
            country: 'long_name',
            postal_code: 'short_name'
        };

        // Reset existing address fields
        document.getElementById('id_address_line1').value = '';
        document.getElementById('id_address_line2').value = '';
        document.getElementById('id_city').value = '';
        document.getElementById('id_county').value = '';
        document.getElementById('id_postcode').value = '';
        document.getElementById('id_country').value = '';

        // Populate address fields
        let streetNumber = '';
        let route = '';

        for (const component of addressComponents) {
            const addressType = component.types[0];
            if (componentForm[addressType]) {
                const val = component[componentForm[addressType]];
                switch (addressType) {
                    case 'street_number':
                        streetNumber = val;
                        break;
                    case 'route':
                        route = val;
                        break;
                    case 'locality':
                        document.getElementById('id_city').value = val;
                        break;
                    case 'administrative_area_level_1':
                        document.getElementById('id_county').value = val;
                        break;
                    case 'postal_code':
                        document.getElementById('id_postcode').value = val;
                        break;
                    case 'country':
                        document.getElementById('id_country').value = val;
                        break;
                    default:
                        break;
                }
            }
        }

        // Combine street number and route for address_line1
        document.getElementById('id_address_line1').value = streetNumber + ' ' + route;
    });
}
