from django.urls import path
from .views import view_dtl, option_data_list, op_scraper

urlpatterns = [
    path('', view_dtl, name='execute_back_test_task'),
    path('test', option_data_list, name='execute_back_test_task'),
    path('op', op_scraper, name='update_op_table')
]
