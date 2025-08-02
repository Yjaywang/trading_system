from celery import shared_task
from datetime import datetime, timedelta
from core.services.scraper import (
    run_op_scraper,
    run_price_scraper,
    run_unfulfilled_op_scraper,
    run_unfulfilled_future_scraper,
)
from core.services.analyzer import (
    run_analysis,
    run_analysis_v2,
    send_this_week_results,
    send_this_month_results,
    send_this_year_results,
    get_risk_condition,
    get_unfulfilled_data,
    run_pre_report_analysis,
    run_post_report_analysis,
)
from core.services.order import open_orders, close_orders
from core.lib.line import push_message
from django.core.cache import cache
from core.utils.constants import DAILY_CRON_STATUS, EMOJI_MAP, DATE_FORMAT_2
from datetime import date
from core.middleware.error_decorators import celery_log_task_status
import copy

default_daily_cron_status = {
    "op_scraper_task": EMOJI_MAP["failure"],
    "price_scraper_task": EMOJI_MAP["failure"],
    "unfulfilled_summary_task": EMOJI_MAP["failure"],
    "analyzer_task": EMOJI_MAP["failure"],
    "open_position_task": EMOJI_MAP["failure"],
    "close_position_task": EMOJI_MAP["failure"],
    "pre_market_report_task": EMOJI_MAP["failure"],
    "post_market_report_task": EMOJI_MAP["failure"],
}


@shared_task(max_retries=0)
@celery_log_task_status
def op_scraper_task():
    run_op_scraper()
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status is None:
        daily_cron_status = copy.deepcopy(default_daily_cron_status)
    daily_cron_status["op_scraper_task"] = EMOJI_MAP["success"]
    cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)


@shared_task(max_retries=0)
@celery_log_task_status
def price_scraper_task():
    run_price_scraper()
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status is None:
        daily_cron_status = copy.deepcopy(default_daily_cron_status)
    daily_cron_status["price_scraper_task"] = EMOJI_MAP["success"]
    cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)


@shared_task(max_retries=0)
@celery_log_task_status
def unfulfilled_data_summary_task():
    run_unfulfilled_op_scraper()
    run_unfulfilled_future_scraper()
    get_unfulfilled_data()
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status is None:
        daily_cron_status = copy.deepcopy(default_daily_cron_status)
    daily_cron_status["unfulfilled_summary_task"] = EMOJI_MAP["success"]
    cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)


@shared_task(max_retries=0)
@celery_log_task_status
def analyzer_task():
    run_analysis_v2()
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status is None:
        daily_cron_status = copy.deepcopy(default_daily_cron_status)
    daily_cron_status["analyzer_task"] = EMOJI_MAP["success"]
    cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)


@shared_task(max_retries=0)
@celery_log_task_status
def open_position_task():
    open_orders()
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status is None:
        daily_cron_status = copy.deepcopy(default_daily_cron_status)
    daily_cron_status["open_position_task"] = EMOJI_MAP["success"]
    cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)


@shared_task(max_retries=0)
@celery_log_task_status
def close_position_task():
    close_orders()
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status is None:
        daily_cron_status = copy.deepcopy(default_daily_cron_status)
    daily_cron_status["close_position_task"] = EMOJI_MAP["success"]
    cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)


@shared_task(
    bind=True, max_retries=2, default_retry_delay=60 * 10
)  # 10 mins after retry
@celery_log_task_status
def pre_market_report_task(self):
    try:
        run_pre_report_analysis()
        daily_cron_status = cache.get(DAILY_CRON_STATUS)
        if daily_cron_status is None:
            daily_cron_status = copy.deepcopy(default_daily_cron_status)
        daily_cron_status["pre_market_report_task"] = EMOJI_MAP["success"]
        cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)
    except Exception as e:
        self.retry(exc=e)


@shared_task(
    bind=True, max_retries=2, default_retry_delay=60 * 10
)  # 10 mins after retry
@celery_log_task_status
def post_market_report_task(self):
    try:
        run_post_report_analysis()
        daily_cron_status = cache.get(DAILY_CRON_STATUS)
        if daily_cron_status is None:
            daily_cron_status = copy.deepcopy(default_daily_cron_status)
        daily_cron_status["post_market_report_task"] = EMOJI_MAP["success"]
        cache.set(DAILY_CRON_STATUS, daily_cron_status, timeout=3600 * 12)
    except Exception as e:
        self.retry(exc=e)


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
def daily_notification_task():
    daily_cron_status = cache.get(DAILY_CRON_STATUS)
    if daily_cron_status:
        messages = []
        for key, value in daily_cron_status.items():
            messages.append(f"{value}: {key}")
        joined_messages = "\n".join(messages)
        formatted_date = date.today().strftime(DATE_FORMAT_2)
        push_message(f"{formatted_date}\n{joined_messages}")
