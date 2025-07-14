from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trading_system.settings")

app = Celery("trading_system")

# load Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# auto discover task
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# @app.task(bind=True, ignore_result=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')
app.conf.update(
    worker_log_format="%(levelname)s %(asctime)s %(module)s %(message)s",
    worker_task_log_format="%(levelname)s %(asctime)s %(module)s %(message)s",
    worker_log_level="INFO",
)
