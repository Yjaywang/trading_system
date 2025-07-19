from notion_client import Client
import os
from datetime import datetime
from ..utils.constants import DATE_FORMAT_2
from ..middleware.error_decorators import core_logger

_notion_client = None
_database_id = None


def get_notion_client() -> Client:
    global _notion_client
    if _notion_client is None:
        token = os.getenv("NOTION_TOKEN")
        if not token:
            raise ValueError("NOTION_TOKEN environment variable not set.")
        _notion_client = Client(auth=token)
    return _notion_client


def get_database_id() -> str:
    global _database_id
    if _database_id is None:
        db_id = os.getenv("NOTION_DATABASE_ID")
        if not db_id:
            raise ValueError("NOTION_DATABASE_ID environment variable not set.")
        _database_id = db_id
    return _database_id


ACTION_MAP = {"Buy": "多", "Sell": "空"}


def insert_trade_record_to_notion(
    open_price: float, close_price: float, quantity: int, direction: str
) -> dict:
    if direction not in ACTION_MAP:
        raise ValueError(f"Invalid direction: {direction}. Must be 'Buy' or 'Sell'.")

    is_profitable = False
    if direction == "Buy":
        is_profitable = close_price > open_price
    elif direction == "Sell":
        is_profitable = close_price < open_price

    status = "獲利" if is_profitable else "虧損"

    new_page_properties = {
        "備註": {"title": [{"text": {"content": status}}]},
        "部位": {"select": {"name": ACTION_MAP[direction]}},
        "口數": {"number": quantity},
        "清倉日期": {"date": {"start": datetime.now().strftime(DATE_FORMAT_2)}},
        "進場點位": {"number": open_price},
        "出場點位": {"number": close_price},
    }

    try:
        notion_client = get_notion_client()
        database_id = get_database_id()
        response = notion_client.pages.create(
            parent={"database_id": database_id},
            properties=new_page_properties,
        )
        core_logger.info("Insert data to Notion succeeded")
        return response
    except Exception as e:
        core_logger.error(f"Insert data to Notion failed: {e}")
