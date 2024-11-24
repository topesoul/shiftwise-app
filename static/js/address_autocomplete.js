// /workspace/shiftwise/static/js/address_autocomplete.js

$(document).ready(function () {
  console.log("initAutocomplete function called.");

  // Select all input fields with the 'address-autocomplete' class
  const $addressInputs = $('input.address-autocomplete');
  console.log(`Found ${$addressInputs.length} address-autocomplete inputs.`);

  $addressInputs.each(function () {
      const input = this;
      const inputId = $(input).attr('id');
      console.log(`Initializing autocomplete for input ID: ${inputId}`);

      // Determine the base ID by removing 'address_line1' from the input's ID
      const baseIdMatch = inputId.match(/^(.*)address_line1$/);
      if (!baseIdMatch) {
          console.error(`Input ID "${inputId}" does not end with 'address_line1'.`);
          return;
      }
      const baseId = baseIdMatch[1];  // e.g., 'id_shift_' or 'id_profile_'

      // Initialize Google Places Autocomplete
      const autocomplete = new google.maps.places.Autocomplete(input, {
          types: ['geocode'], // Restrict results to addresses
          componentRestrictions: { country: ['uk'] } // Restrict to UK addresses
      });

      // Specify the fields to retrieve from the Place object
      autocomplete.setFields(['address_component', 'geometry']);

      // Add listener for place selection
      autocomplete.addListener('place_changed', function () {
          console.log(`Place changed for input ID: ${inputId}`);
          const place = autocomplete.getPlace();

          if (place.geometry && place.geometry.location) {
              console.log(`Geocoded location: ${place.geometry.location.lat()}, ${place.geometry.location.lng()}`);

              // Construct IDs for address fields
              const addressLine1Id = baseId + 'address_line1';
              const addressLine2Id = baseId + 'address_line2';
              const cityId = baseId + 'city';
              const countyId = baseId + 'county';
              const postcodeId = baseId + 'postcode';
              const countryId = baseId + 'country';
              const latFieldId = baseId + 'latitude';
              const lngFieldId = baseId + 'longitude';

              // Get the address fields using jQuery
              const $addressLine1Field = $('#' + addressLine1Id);
              const $addressLine2Field = $('#' + addressLine2Id);
              const $cityField = $('#' + cityId);
              const $countyField = $('#' + countyId);
              const $postcodeField = $('#' + postcodeId);
              const $countryField = $('#' + countryId);
              const $latField = $('#' + latFieldId);
              const $lngField = $('#' + lngFieldId);

              // Reset the fields
              $addressLine1Field.val('');
              $addressLine2Field.val('');
              $cityField.val('');
              $countyField.val('');
              $postcodeField.val('');
              $countryField.val('UK'); // Default to UK

              // Get each component of the address from the place details
              place.address_components.forEach(function (component) {
                  const componentType = component.types[0];

                  switch (componentType) {
                      case 'street_number':
                          $addressLine1Field.val(component.long_name + ' ' + $addressLine1Field.val());
                          break;
                      case 'route':
                          $addressLine1Field.val($addressLine1Field.val() + component.long_name);
                          break;
                      case 'locality':
                          $cityField.val(component.long_name);
                          break;
                      case 'administrative_area_level_2':
                          $countyField.val(component.long_name);
                          break;
                      case 'postal_code':
                          $postcodeField.val(component.long_name);
                          break;
                      case 'country':
                          $countryField.val(component.long_name);
                          break;
                  }
              });

              // Set latitude and longitude
              if ($latField.length && $lngField.length) {
                  $latField.val(place.geometry.location.lat());
                  $lngField.val(place.geometry.location.lng());
                  console.log(`Latitude set to: ${$latField.val()}, Longitude set to: ${$lngField.val()}`);
              } else {
                  console.error(`Latitude or Longitude field not found for base ID: "${baseId}". Expected IDs: "${latFieldId}" and "${lngFieldId}".`);
              }
          } else {
              console.log(`No geometry available for input: '${place.name}'`);
          }
      });
  });
});