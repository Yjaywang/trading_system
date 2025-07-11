from celery import shared_task
from datetime import datetime, timedelta
from .services.scraper import (
    run_op_scraper,
    run_price_scraper,
    run_unfulfilled_op_scraper,
    run_unfulfilled_future_scraper,
)
from .services.analyzer import (
    run_analysis,
    send_this_week_results,
    send_this_month_results,
    send_this_year_results,
    get_risk_condition,
    get_unfulfilled_data,
)
from .services.order import open_orders, close_orders
from .services.line import push_message
from django.core.cache import cache
from .utils.constants import DAILY_CRON_STATUS, EMOJI_MAP, DATE_FORMAT_2
from datetime import date
from .middleware.error_decorators import celery_log_task_status

default_daily_cron_status = {
    "op_scraper_task": EMOJI_MAP["failure"],
    "price_scraper_task": EMOJI_MAP["failure"],
    "unfulfilled_op_scraper_task": EMOJI_MAP["failure"],
    "unfulfilled_future_scraper_task": EMOJI_MAP["failure"],
    "analyzer_task": EMOJI_MAP["failure"],
    "open_position_task": EMOJI_MAP["failure"],
    "close_position_task": EMOJI_MAP["failure"],
}


@shared_task(max_retries=0)
@celery_log_task_status
def op_scraper_task():
    run_op_scraper()
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status is None:
        daily_cron_status = default_daily_cron_status.copy()
    daily_cron_status["op_scraper_task"] = EMOJI_MAP["success"]
    cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)


@shared_task(max_retries=0)
@celery_log_task_status
def price_scraper_task():
    run_price_scraper()
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status is None:
        daily_cron_status = default_daily_cron_status.copy()
    daily_cron_status["price_scraper_task"] = EMOJI_MAP["success"]
    cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)


@shared_task(max_retries=0)
@celery_log_task_status
def unfulfilled_op_scraper_task():
    run_unfulfilled_op_scraper()
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status is None:
        daily_cron_status = default_daily_cron_status.copy()
    daily_cron_status["unfulfilled_op_scraper_task"] = EMOJI_MAP["success"]
    cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)


@shared_task(max_retries=0)
@celery_log_task_status
def unfulfilled_future_scraper_task():
    run_unfulfilled_future_scraper()
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status is None:
        daily_cron_status = default_daily_cron_status.copy()
    daily_cron_status["unfulfilled_future_scraper_task"] = EMOJI_MAP["success"]
    cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)


@shared_task(max_retries=0)
@celery_log_task_status
def analyzer_task():
    run_analysis()
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status is None:
        daily_cron_status = default_daily_cron_status.copy()
    daily_cron_status["analyzer_task"] = EMOJI_MAP["success"]
    cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)


@shared_task(max_retries=0)
@celery_log_task_status
def open_position_task():
    open_orders()
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status is None:
        daily_cron_status = default_daily_cron_status.copy()
    daily_cron_status["open_position_task"] = EMOJI_MAP["success"]
    cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)


@shared_task(max_retries=0)
@celery_log_task_status
def close_position_task():
    close_orders()
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status is None:
        daily_cron_status = default_daily_cron_status.copy()
    daily_cron_status["close_position_task"] = EMOJI_MAP["success"]
    cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)


@shared_task
def check_and_notify_month_end():
    today = datetime.today()
    if (today + timedelta(days=1)).day == 1:
        notify_this_month_revenue_task()


@shared_task(max_retries=0)
@celery_log_task_status
def notify_this_week_revenue_task():
    send_this_week_results()


@shared_task(max_retries=0)
@celery_log_task_status
def notify_this_month_revenue_task():
    send_this_month_results()


@shared_task(max_retries=0)
@celery_log_task_status
def notify_this_year_revenue_task():
    send_this_year_results()


@shared_task(max_retries=0)
@celery_log_task_status
def check_risk_task():
    get_risk_condition()


@shared_task(max_retries=0)
@celery_log_task_status
def generate_unfulfilled_data():
    get_unfulfilled_data()


@shared_task(max_retries=0)
@celery_log_task_status
def daily_notification_task():
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status:
        messages = []
        for key, value in daily_cron_status.items():
            messages.append(f"{value}: {key}")
        joined_messages = "\n".join(messages)
        formatted_date = date.today().strftime(DATE_FORMAT_2)
        push_message(f"{formatted_date}\n{joined_messages}")
