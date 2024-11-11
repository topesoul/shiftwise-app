# /workspace/shiftwise/shiftwise/celery.py

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shiftwise.settings")

app = Celery("shiftwise")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
