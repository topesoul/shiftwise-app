// /workspace/shiftwise/static/js/modal_control.js

document.addEventListener('DOMContentLoaded', function () {
    // Check if the modal should be opened
    if (window.OPEN_MODAL) {
        $('#updateProfileModal').modal('show');
    }
});
