// /workspace/shiftwise/shifts/static/shifts/js/shift_complete_modal.js

document.addEventListener("DOMContentLoaded", function () {
    const signaturePadCanvas = document.getElementById("signaturePad");
    const signatureInput = document.querySelector(".signatureInput");
    const clearSignatureButton = document.querySelector(".clearSignature");
    const getLocationButton = document.querySelector(".getLocation");
    const locationStatus = document.getElementById("locationStatus");
    const confirmAddressInput = document.getElementById("id_confirm_address");
    const latitudeInput = document.getElementById("id_latitude");
    const longitudeInput = document.getElementById("id_longitude");

    const signaturePad = new SignaturePad(signaturePadCanvas, {
        backgroundColor: "rgba(255, 255, 255, 0)", // Transparent background
    });

    // Clear Signature
    clearSignatureButton.addEventListener("click", function () {
        signaturePad.clear();
        signatureInput.value = "";
    });

    // Capture Signature on Form Submission
    const completeShiftForm = document.getElementById("completeShiftForm");
    completeShiftForm.addEventListener("submit", function (e) {
        if (signaturePad.isEmpty()) {
            e.preventDefault();
            alert("Please provide a signature before submitting.");
        } else {
            const dataURL = signaturePad.toDataURL("image/png");
            signatureInput.value = dataURL;
        }
    });

    // Get Current Location
    getLocationButton.addEventListener("click", function () {
        if (!navigator.geolocation) {
            locationStatus.innerHTML = "<span class='text-danger'>Geolocation is not supported by your browser.</span>";
            return;
        }

        locationStatus.innerHTML = "<span class='text-info'>Locating...</span>";

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const latitude = position.coords.latitude.toFixed(6);
                const longitude = position.coords.longitude.toFixed(6);
                latitudeInput.value = latitude;
                longitudeInput.value = longitude;
                locationStatus.innerHTML = `<span class='text-success'>Location captured: (${latitude}, ${longitude})</span>`;

                // Fetch address using reverse geocoding 
                fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`)
                    .then((response) => response.json())
                    .then((data) => {
                        const address = data.display_name || "Address not found.";
                        confirmAddressInput.value = address;
                    })
                    .catch((error) => {
                        console.error("Error fetching address:", error);
                        confirmAddressInput.value = "Unable to retrieve address.";
                    });
            },
            () => {
                locationStatus.innerHTML = "<span class='text-danger'>Unable to retrieve your location.</span>";
            }
        );
    });
});
