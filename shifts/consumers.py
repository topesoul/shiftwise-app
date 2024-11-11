# /workspace/shiftwise/shifts/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            self.group_name = f"user_{user.id}"
            # Join group
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if user.is_authenticated:
            # Leave group
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Receive message from group
    async def send_notification(self, event):
        message = event["message"]
        icon = event.get("icon", "fas fa-info-circle")
        url = event.get("url", "")
        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "icon": icon,
                    "url": url,
                }
            )
        )
