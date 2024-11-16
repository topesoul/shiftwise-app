// /workspace/shiftwise/static/js/notification.js

document.querySelectorAll('.mark-read-btn').forEach(button => {
    button.addEventListener('click', function() {
        const notificationId = this.getAttribute('data-id');
        fetch("{% url 'notifications:mark_notification_read' 0 %}".replace('0', notificationId), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            },
        })
        .then(response => response.json())
        .then(data => {
            if(data.success){
                this.parentElement.style.textDecoration = "line-through";
                this.remove();
            } else {
                alert(data.message);
            }
        })
        .catch(error => console.error('Error:', error));
    });
});
