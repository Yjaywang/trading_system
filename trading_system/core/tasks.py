from celery import shared_task
from .services.scraper import run_op_scraper, run_price_scraper
from .services.analyzer import run_analysis
from .services.order import open_orders, close_orders
from .services.line import push_message


@shared_task(max_retries=0)
def op_scraper_task():
    try:
        run_op_scraper()
        push_message('test op scraper')
    except Exception as e:
        print(f"Error in op_scraper_task: {e}")


@shared_task(max_retries=0)
def price_scraper_task():
    try:
        run_price_scraper()
        push_message('test price scraper')
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


@shared_task(max_retries=0)
def cron_test():
    push_message('cron test')
