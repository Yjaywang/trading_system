import requests
import os
from dotenv import load_dotenv
from ..utils.constants import LINE_BUBBLE_MESSAGE_TEMPLATE
from ..types import BubbleMessage
from distutils.util import strtobool
from ..middleware.error_decorators import core_logger

load_dotenv()


def push_message(message):
    if not bool(strtobool(os.getenv("LINE_NOTIFY", "False"))):
        return
    url = f"{os.getenv('LINE_PUSH_MESSAGE_URL')}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('LINE_CHANNEL_ACCESS_TOKEN')}",
    }
    data = {
        "to": os.getenv("LINE_USER_ID"),
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
    if not bool(strtobool(os.getenv("LINE_NOTIFY", "False"))):
        return
    bubble_message = LINE_BUBBLE_MESSAGE_TEMPLATE.copy()
    bubble_message["header"]["contents"][0]["text"] = message.get("header", "")
    bubble_message["body"]["contents"][0]["text"] = message.get("body", "")
    if "footer" not in message:
        del bubble_message["footer"]
    else:
        bubble_message["footer"]["contents"][0]["text"] = message.get("footer", "")

    url = f"{os.getenv('LINE_PUSH_MESSAGE_URL')}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('LINE_CHANNEL_ACCESS_TOKEN')}",
    }
    data = {"to": os.getenv("LINE_USER_ID"), "messages": [bubble_message]}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # 4xx 5xx error
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        core_logger.error(f"LINE HTTP error occurred: {http_err}")
    except Exception as err:
        core_logger.error(f"LINE Other error occurred: {err}")
