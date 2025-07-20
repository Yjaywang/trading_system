import requests
from core.utils.constants import (
    LINE_BUBBLE_MESSAGE_TEMPLATE,
    LINE_BUBBLE_MESSAGE_BODY_CONTENT_TEMPLATE,
)
from core.types import BubbleMessage
from core.middleware.error_decorators import core_logger
import copy
from django.conf import settings


def push_message(message):
    if not settings.LINE_NOTIFY:
        return
    url = f"{settings.LINE_PUSH_MESSAGE_URL}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
    }
    data = {
        "to": settings.LINE_USER_ID,
        "messages": [{"type": "text", "text": f"{message}"}],
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # 4xx 5xx error
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        core_logger.error(f"LINE HTTP error occurred: {http_err}")
    except Exception as err:
        core_logger.error(f"LINE Other error occurred: {err}")


def push_bubble_message(message: BubbleMessage):
    if not settings.LINE_NOTIFY:
        return
    bubble_message = copy.deepcopy(LINE_BUBBLE_MESSAGE_TEMPLATE)
    bubble_message["header"]["contents"][0]["text"] = message.get("header", "")
    for content in message.get("body", []):
        body_content = copy.deepcopy(LINE_BUBBLE_MESSAGE_BODY_CONTENT_TEMPLATE)
        body_content["text"] = content
        bubble_message["body"]["contents"].append(body_content)
    if "footer" not in message:
        del bubble_message["footer"]
    else:
        bubble_message["footer"]["contents"][0]["text"] = message.get("footer", "")
    url = f"{settings.LINE_PUSH_MESSAGE_URL}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
    }
    data = {
        "to": settings.LINE_USER_ID,
        "messages": [
            {
                "type": "flex",
                "altText": message.get("header", "default alt text"),
                "contents": bubble_message,
            }
        ],
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # 4xx 5xx error
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        core_logger.error(f"LINE HTTP error occurred: {http_err}")
    except Exception as err:
        core_logger.error(f"LINE Other error occurred: {err}")
