import logging
from functools import wraps

celery_logger = logging.getLogger('celery')
core_logger = logging.getLogger('core')


def celery_log_task_status(func):
    """
    A decorator to automatically log the success or failure status of a Celery task.

    - On success: logs info with message 'Task {function_name} Succeeded.'
    - On failure: logs error with message 'Task {function_name} Failed: {error}'
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        task_name = func.__name__
        try:
            result = func(*args, **kwargs)
            celery_logger.info(f"Task '{task_name}' Succeeded.")
            return result
        except Exception as e:
            celery_logger.error(f"Task '{task_name}' Failed: {e}")
            raise

    return wrapper


def core_log_task_status(func):
    """
    A decorator to automatically log the success or failure status of Core.

    - On success: logs info with message 'Task {function_name} Succeeded.'
    - On failure: logs error with message 'Task {function_name} Failed: {error}'
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        task_name = func.__name__
        try:
            result = func(*args, **kwargs)
            celery_logger.info(f"'{task_name}' Succeeded.")
            return result
        except Exception as e:
            celery_logger.error(f"'{task_name}' Failed: {e}")
            raise

    return wrapper
