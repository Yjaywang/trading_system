from celery import shared_task
from .services.scraper import run_op_scraper, run_price_scraper
from .services.analyzer import run_analysis
from .services.order import place_orders, close_orders
from .services.line import push_message


@shared_task
def op_scraper_task():
    run_op_scraper()
    push_message('test op scraper')


@shared_task
def price_scraper_task():
    run_price_scraper()
    push_message('test price scraper')


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
def cron_test():
    # push_message('cron test')
    pass
