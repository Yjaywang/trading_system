import requests
import os
from dotenv import load_dotenv

load_dotenv()


def push_message(message):
    url = f"{os.getenv('LINE_PUSH_MESSAGE_URL')}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('LINE_CHANNEL_ACCESS_TOKEN')}",
    }
    data = {"to": os.getenv('LINE_USER_ID'), "messages": [{"type": "text", "text": f"{message}"}]}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() # 4xx 5xx error
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"LINE HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"LINE Other error occurred: {err}")


def analysis_result(message):
    return push_message(message)


def order_result(message):
    return push_message(message)


def close_result(message):
    return push_message(message)
