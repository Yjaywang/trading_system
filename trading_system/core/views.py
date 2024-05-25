from django.shortcuts import render
from django.http import JsonResponse
from core.services.tasks import sample_task


def execute_back_test_task(request):
    result = sample_task.delay(10, 20)
    return JsonResponse({
        'task_id': result.id,
        'task_state': result.state,
    })
