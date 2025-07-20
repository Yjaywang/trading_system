from datetime import datetime
from core.models import Signal
from core.serializers import OrderSerializer, SignalSerializer, RevenueSerializer
from core.utils.constants import WEEKDAY_TRANSFORM, DATE_FORMAT, POINT_VALUE, EMOJI_MAP
from core.utils.trump_words import (
    TRUMP_STYLE_FUNNY_TRADE_BLESSINGS,
    TRUMP_STYLE_TRADING_CONGRATS,
    TRUMP_STYLE_LOSS_COMFORTS,
)
from core.lib.line import push_message, push_bubble_message
from core.lib.shioaji import open_position, close_position, close_some_position
from core.types import BubbleMessage
import random
from core.middleware.error_decorators import core_logger
from django.core.cache import cache
from core.lib.notion import insert_trade_record_to_notion
from django.conf import settings


def _get_today_date_info():
    today_date = datetime.today()
    today_date_str = today_date.strftime(DATE_FORMAT)
    date_pieces = today_date_str.split("/")
    today_day = WEEKDAY_TRANSFORM[today_date.weekday()]
    return today_date_str, date_pieces, today_day


def _record_deal(deal, contract_code, action):
    today_date_str, date_pieces, today_day = _get_today_date_info()
    order_data_obj = {
        "year": date_pieces[0],
        "month": date_pieces[1],
        "date": today_date_str,
        "day": today_day,
        "product": contract_code,
        "quantity": deal["quantity"],
        "action": action,
        "deal_price": deal["price"],
    }
    serializer = OrderSerializer(data=order_data_obj)
    if serializer.is_valid():
        serializer.save()
    else:
        core_logger.error(f"Order serialization failed: {serializer.errors}")


def _record_revenue(deal, contract_code, action):
    today_date_str, date_pieces, today_day = _get_today_date_info()
    cost_price = deal["cost_price"]
    price = deal["price"]
    quantity = deal["quantity"]
    direction = "Buy" if action == "Sell" else "Sell"
    gain_price = price - cost_price if direction == "Buy" else -1 * (price - cost_price)
    revenue = gain_price * quantity * POINT_VALUE[contract_code]
    revenue_data_obj = {
        "year": date_pieces[0],
        "month": date_pieces[1],
        "date": today_date_str,
        "day": today_day,
        "product": contract_code,
        "quantity": quantity,
        "direction": direction,
        "open_price": cost_price,
        "close_price": price,
        "gain_price": gain_price,
        "revenue": revenue,
    }
    serializer = RevenueSerializer(data=revenue_data_obj)
    if serializer.is_valid():
        serializer.save()
        return revenue_data_obj
    else:
        core_logger.error(f"Revenue serialization failed: {serializer.errors}")
        return None


def open_orders():
    try:
        latest_signal_data = Signal.objects.latest("created_at")
        serializer = SignalSerializer(latest_signal_data)
        data = dict(serializer.data)
        if data["date"] is None:
            trading_signal = data["trading_signal"]
            action = {1: "Buy", -1: "Sell"}.get(trading_signal, None)
            contract_code = settings.PRODUCT_CODE
            quantity = settings.PRODUCT_QUANTITY
            if trading_signal is not None and quantity != 0:
                deal_result = open_position(contract_code, action, quantity)
                if deal_result is not None:
                    bubble_message: BubbleMessage = {
                        "header": f" Deal start",
                        "body": [
                            f"1. {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}",
                            f"2. Product: {deal_result['product']}",
                            f"3. Action: {deal_result['action']}",
                            f"4. Avg Price: {deal_result['price']}",
                            f"5. Quantity: {deal_result['quantity']}",
                        ],
                        "footer": f"{random.choice(TRUMP_STYLE_FUNNY_TRADE_BLESSINGS)}",
                    }
                    push_bubble_message(bubble_message)
                    _record_deal(deal_result, contract_code, action)
                else:
                    message = "Deal is in trouble, please check your account"
                    core_logger.error(message)
                    cache.set(
                        "sj_error",
                        (cache.get("sj_error") or []) + [message],
                        timeout=3600,
                    )
            else:
                message = "Signal is none, please check db"
                core_logger.error(message)
                cache.set(
                    "sj_error", (cache.get("sj_error") or []) + [message], timeout=3600
                )
        else:
            message = "Not latest signal, please check db"
            core_logger.error(message)
            cache.set(
                "sj_error", (cache.get("sj_error") or []) + [message], timeout=3600
            )
    except Exception as e:
        message = f"Place order error: {e}"
        core_logger.error(message)
        cache.set("sj_error", (cache.get("sj_error") or []) + [message], timeout=3600)
    finally:
        # push sj error message
        sj_error_messages = cache.get("sj_error")
        if sj_error_messages:
            message = "\n\n".join(sj_error_messages)
            push_message(message)
            cache.delete("sj_error")


def close_orders():
    try:
        contract_code = settings.PRODUCT_CODE
        deal_result = close_position(contract_code)
        if deal_result is not None:
            action = deal_result["action"]
            _record_deal(deal_result, contract_code, action)
            revenue_data = _record_revenue(deal_result, contract_code, action)
            if revenue_data is not None:
                bubble_message: BubbleMessage = {
                    "header": "Today's revenue",
                    "body": [
                        f"1. {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}",
                        f"2. product: {contract_code}",
                        f"3. quantity: {revenue_data['quantity']}",
                        f"4. direction: {revenue_data['direction']}",
                        f"5. open_price: {revenue_data['open_price']}",
                        f"6. close_price: {revenue_data['close_price']}",
                        f"7. gain_price: {revenue_data['gain_price']}",
                        f"8. revenue: {revenue_data['revenue']}",
                    ],
                    "footer": (
                        f"{EMOJI_MAP['profit']} {random.choice(TRUMP_STYLE_TRADING_CONGRATS)}"
                        if revenue_data["revenue"] > 0
                        else f"{EMOJI_MAP['loss']} {random.choice(TRUMP_STYLE_LOSS_COMFORTS)}"
                    ),
                }
                push_bubble_message(bubble_message)

                insert_trade_record_to_notion(
                    revenue_data["open_price"],
                    revenue_data["close_price"],
                    revenue_data["quantity"],
                    revenue_data["direction"],
                )
        else:
            message = "Deal is in trouble, please check your account"
            core_logger.error(message)
            cache.set(
                "sj_error", (cache.get("sj_error") or []) + [message], timeout=3600
            )
    except Exception as e:
        message = f"Close order error: {e}"
        core_logger.error(message)
        cache.set("sj_error", (cache.get("sj_error") or []) + [message], timeout=3600)
    finally:
        # push sj error message
        sj_error_messages = cache.get("sj_error")
        if sj_error_messages:
            message = "\n\n".join(sj_error_messages)
            push_message(message)
            cache.delete("sj_error")


def open_some_orders(quantity):
    try:
        latest_signal_data = Signal.objects.latest("created_at")
        serializer = SignalSerializer(latest_signal_data)
        data = dict(serializer.data)
        if data["date"] is None:
            trading_signal = data["trading_signal"]
            action = {1: "Buy", -1: "Sell"}.get(trading_signal, None)
            contract_code = settings.PRODUCT_CODE
            if trading_signal is not None and quantity != 0:
                deal_result = open_position(contract_code, action, quantity)
                if deal_result is not None:
                    bubble_message: BubbleMessage = {
                        "header": f" Deal start",
                        "body": [
                            f"1. {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}",
                            f"2. Product: {deal_result['product']}",
                            f"3. Action: {deal_result['action']}",
                            f"4. Avg Price: {deal_result['price']}",
                            f"5. Quantity: {deal_result['quantity']}",
                        ],
                        "footer": f"{random.choice(TRUMP_STYLE_FUNNY_TRADE_BLESSINGS)}",
                    }
                    push_bubble_message(bubble_message)
                    _record_deal(deal_result, contract_code, action)
                else:
                    message = "Deal is in trouble, please check your account"
                    core_logger.error(message)
                    cache.set(
                        "sj_error",
                        (cache.get("sj_error") or []) + [message],
                        timeout=3600,
                    )
            else:
                message = "Signal is none, please check db"
                core_logger.error(message)
                cache.set(
                    "sj_error", (cache.get("sj_error") or []) + [message], timeout=3600
                )
        else:
            message = "Not latest signal, please check db"
            core_logger.error(message)
            cache.set(
                "sj_error", (cache.get("sj_error") or []) + [message], timeout=3600
            )
    except Exception as e:
        message = f"Place order error: {e}"
        core_logger.error(message)
        cache.set("sj_error", (cache.get("sj_error") or []) + [message], timeout=3600)
    finally:
        # push sj error message
        sj_error_messages = cache.get("sj_error")
        if sj_error_messages:
            message = "\n\n".join(sj_error_messages)
            push_message(message)
            cache.delete("sj_error")


def close_some_orders(quantity):
    try:
        contract_code = settings.PRODUCT_CODE
        deal_result = close_some_position(contract_code, quantity)
        if deal_result is not None:
            action = deal_result["action"]
            _record_deal(deal_result, contract_code, action)
            revenue_data = _record_revenue(deal_result, contract_code, action)
            if revenue_data is not None:
                bubble_message: BubbleMessage = {
                    "header": "Today's some revenue",
                    "body": [
                        f"1. {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}",
                        f"2. product: {contract_code}",
                        f"3. quantity: {revenue_data['quantity']}",
                        f"4. direction: {revenue_data['direction']}",
                        f"5. open_price: {revenue_data['open_price']}",
                        f"6. close_price: {revenue_data['close_price']}",
                        f"7. gain_price: {revenue_data['gain_price']}",
                        f"8. revenue: {revenue_data['revenue']}",
                    ],
                    "footer": (
                        f"{EMOJI_MAP['profit']} {random.choice(TRUMP_STYLE_TRADING_CONGRATS)}"
                        if revenue_data["revenue"] > 0
                        else f"{EMOJI_MAP['loss']} {random.choice(TRUMP_STYLE_LOSS_COMFORTS)}"
                    ),
                }
                push_bubble_message(bubble_message)
                insert_trade_record_to_notion(
                    revenue_data["open_price"],
                    revenue_data["close_price"],
                    revenue_data["quantity"],
                    revenue_data["direction"],
                )
        else:
            message = "Deal is in trouble, please check your account"
            core_logger.error(message)
            cache.set(
                "sj_error", (cache.get("sj_error") or []) + [message], timeout=3600
            )
    except Exception as e:
        message = f"Close order error: {e}"
        core_logger.error(message)
        cache.set("sj_error", (cache.get("sj_error") or []) + [message], timeout=3600)
    finally:
        # push sj error message
        sj_error_messages = cache.get("sj_error")
        if sj_error_messages:
            message = "\n\n".join(sj_error_messages)
            push_message(message)
            cache.delete("sj_error")
