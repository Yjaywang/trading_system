from celery import shared_task
from .scraper import run_op_scraper
from .analyzer import run_analysis
from .order import place_orders, close_orders


@shared_task
def scraper_task():
    run_op_scraper()


@shared_task
def analyzer_task():
    run_analysis()


@shared_task
def order_task():
    place_orders()


@shared_task
def close_task():
    close_orders()


@shared_task
def sample_task(arg1, arg2):
    print(f'This is a sample task with arguments: {arg1}, {arg2}')
    return arg1 + arg2
