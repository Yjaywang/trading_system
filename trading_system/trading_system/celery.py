from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')

app = Celery('trading_system')

# load Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# auto discover task
app.autodiscover_tasks()

# set taiwan time
app.conf.update(timezone='Asia/Taipei')
