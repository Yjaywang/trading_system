from django.urls import path
from .views import execute_back_test_task

urlpatterns = [
    path('execute-task/', execute_back_test_task, name='execute_back_test_task'),
]
