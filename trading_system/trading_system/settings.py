"""
Django settings for trading_system project.

Generated by 'django-admin startproject' using Django 5.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from celery.schedules import crontab

load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
TRADING_SECRET_TOKEN = os.getenv('TRADING_SECRET_TOKEN')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False if os.getenv('APP_ENV') == 'production' else True

ALLOWED_HOSTS = os.getenv('ALLOW_DOMAIN', 'localhost,127.0.0.1').split(',')

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "trading_system.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "trading_system.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

#  taiwan time
TIME_ZONE = 'Asia/Taipei'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Celery settings
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Taipei' # set taiwan time

CELERY_BEAT_SCHEDULE = {
    'op-scraper-task': {
        'task': 'core.tasks.op_scraper_task',
        'schedule': crontab(minute='10', hour='14', day_of_week='1-5'),                     # Mon to Fri 14:10
    },
    'price-scraper-task': {
        'task': 'core.tasks.price_scraper_task',
        'schedule': crontab(minute='0', hour='16', day_of_week='1-5'),                      # Mon to Fri 16:00
    },
    'analyze-signal-task': {
        'task': 'core.tasks.analyzer_task',
        'schedule': crontab(minute='20', hour='14', day_of_week='1-5'),                     # Mon to Fri 14:20
    },
    'open-order-task': {
        'task': 'core.tasks.open_position_task',
        'schedule': crontab(minute='0', hour='15', day_of_week='1-5'),                      # Mon to Fri 15:00
    },
    'close-order-task': {
        'task': 'core.tasks.close_position_task',
        'schedule': crontab(minute='44', hour='13', day_of_week='1-5'),                     # Mon to Fri 13:44
    },
    'weekly-notify-revenue-task': {
        'task': 'core.tasks.notify_this_week_revenue_task',
        'schedule': crontab(minute='0', hour='17', day_of_week='5'),                        # Fri 17:00
    },
    'monthly-notify-revenue-task': {
        'task': 'core.tasks.check_and_notify_month_end',
        'schedule': crontab(minute='10', hour='17'),                                        # 17:10
    },
    'yearly-notify-revenue-task': {
        'task': 'core.tasks.notify_this_year_revenue_task',
        'schedule': crontab(minute='20', hour='17', day_of_month='31', month_of_year='12'), # Year end 17:20
    },
    'gc-taks-task': {
        'task': 'core.tasks.clear_memory',
        'schedule': crontab(minute='30', hour='*'),                                         # every hour:30
    },
    'check-risk-task': {
        'task': 'core.tasks.check_risk_task',
        'schedule': crontab(minute='45', hour='*'),                                         # every hour:45
    },

                                                                                              # 'cron-task': {
                                                                                              #     'task': 'core.tasks.cron_test',
                                                                                              #     'schedule': crontab(minute='*', hour='*', day_of_week='1-5'),   # Mon to Fri 13:44
                                                                                              # },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/logs/core_info.log',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
