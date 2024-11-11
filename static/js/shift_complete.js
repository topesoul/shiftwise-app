// /workspace/shiftwise/static/js/shift_complete.js

/**
 * Handle Shift Completion Features:
 * - Initialize Signature Pad
 * - Clear Signature
 * - Capture Signature on Form Submit
 * - Get Current Location and Populate Latitude and Longitude
 */

document.addEventListener('DOMContentLoaded', function () {
    // Initialize Signature Pad
    const signatureCanvas = document.getElementById('signaturePad');
    if (signatureCanvas) {
        const signaturePad = new SignaturePad(signatureCanvas, {
            penColor: '#000',
            backgroundColor: '#fff'
        });

        const clearButton = document.querySelector('.clearSignature');
        const signatureInput = document.querySelector('.signatureInput');

        // Clear Signature
        if (clearButton) {
            clearButton.addEventListener('click', function () {
                signaturePad.clear();
                if (signatureInput) {
                    signatureInput.value = '';
                }
            });
        }

        // Capture Signature on Form Submit
        const completeShiftForm = document.getElementById('completeShiftForm');
        if (completeShiftForm) {
            completeShiftForm.addEventListener('submit', function (e) {
                if (signaturePad.isEmpty()) {
                    e.preventDefault();
                    alert('Please provide a signature.');
                    return;
                }
                const dataURL = signaturePad.toDataURL();
                if (signatureInput) {
                    signatureInput.value = dataURL;
                }
            });
        }
    } else {
        console.error("Signature Pad canvas with id 'signaturePad' not found.");
    }

    // Get Current Location
    const getLocationButton = document.querySelector('.getLocation');
    const locationStatus = document.getElementById('locationStatus');
    const latitudeInput = document.getElementById('id_latitude');
    const longitudeInput = document.getElementById('id_longitude');

    if (getLocationButton && latitudeInput && longitudeInput && locationStatus) {
        getLocationButton.addEventListener('click', function () {
            if (navigator.geolocation) {
                locationStatus.innerHTML = '<span class="text-info">Fetching location...</span>';
                navigator.geolocation.getCurrentPosition(function (position) {
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;
                    latitudeInput.value = latitude;
                    longitudeInput.value = longitude;
                    locationStatus.innerHTML = `<span class="text-success">Location acquired: (${latitude.toFixed(5)}, ${longitude.toFixed(5)})</span>`;
                }, function (error) {
                    locationStatus.innerHTML = '<span class="text-danger">Unable to retrieve your location.</span>';
                });
            } else {
                locationStatus.innerHTML = '<span class="text-danger">Geolocation is not supported by your browser.</span>';
            }
        });
    } else {
        console.error("Required elements for geolocation are missing.");
    }
});
