from celery import shared_task
from datetime import datetime, timedelta
from .services.scraper import run_op_scraper, run_price_scraper
from .services.analyzer import run_analysis, send_this_week_results, send_this_month_results, send_this_year_results
from .services.order import open_orders, close_orders
from .services.line import push_message
import gc


@shared_task(max_retries=0)
def clear_memory():
    print("gc cron start")
    gc.collect()
    print("gc cron done")


@shared_task(max_retries=0)
def op_scraper_task():
    try:
        run_op_scraper()
        push_message('op scraper done')
    except Exception as e:
        print(f"Error in op_scraper_task: {e}")


@shared_task(max_retries=0)
def price_scraper_task():
    try:
        run_price_scraper()
        push_message('price scraper done')
    except Exception as e:
        print(f"Error in price_scraper_task: {e}")


@shared_task(max_retries=0)
def analyzer_task():
    try:
        run_analysis()
    except Exception as e:
        print(f"Error in analyzer_task: {e}")


@shared_task(max_retries=0)
def open_position_task():
    try:
        open_orders()
    except Exception as e:
        print(f"Error in open_position_task: {e}")


@shared_task(max_retries=0)
def close_position_task():
    try:
        close_orders()
    except Exception as e:
        print(f"Error in close_position_task: {e}")


@shared_task
def check_and_notify_month_end():
    today = datetime.today()
    if (today + timedelta(days=1)).day == 1:
        notify_this_month_revenue_task()


@shared_task(max_retries=0)
def notify_this_week_revenue_task():
    try:
        send_this_week_results()
    except Exception as e:
        print(f"Error in notify_this_week_revenue_task: {e}")


@shared_task(max_retries=0)
def notify_this_month_revenue_task():
    try:
        send_this_month_results()
    except Exception as e:
        print(f"Error in notify_this_month_revenue_task: {e}")


@shared_task(max_retries=0)
def notify_this_year_revenue_task():
    try:
        send_this_year_results()
    except Exception as e:
        print(f"Error in notify_this_year_revenue_task: {e}")


@shared_task(max_retries=0)
def cron_test():
    push_message('cron test')
