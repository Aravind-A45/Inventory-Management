# celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory.settings')

# Create a Celery instance and configure it using the settings from Django.
app = Celery('inventory')
app.conf.enable_utc = False

app.conf.update(timezone='Asia/Kolkata')

# Load task modules from all registered Django app configs.
app.conf.beat_schedule = {
    'send-mail-every-day-at-8': {
        'task': 'invention.tasks.send_notification_mail',
        'schedule': crontab(hour=18, minute=17),
    },
    'send-mail-every-day-at-2': {
        'task': 'invention.tasks.send_warning_mail',
        'schedule': crontab(hour=18, minute=25),
    },
    'send-mail-every-day-at-3': {
        'task': 'invention.tasks.send_stock_mail',
        'schedule': crontab(hour=18, minute=24),
    }
}

app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
