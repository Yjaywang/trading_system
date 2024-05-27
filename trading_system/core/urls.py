from django.urls import path
from .views import view_dtl, option_data_list, op_scraper, price_scraper, settlement, test, analysis, order

urlpatterns = [
    path('', view_dtl, name='execute_back_test_task'),
    path('test', test, name='execute_back_test_task'),
    path('op', op_scraper, name='update_op_table'),
    path('price', price_scraper, name='update_price_table'),
    path('settlement', settlement, name='insert_settlement'),
    path('analysis', analysis, name='analysis_signal'),
    path('order', order, name='order')
]
