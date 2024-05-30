import os
from datetime import datetime
from ..models import Signal, Order
from ..serializers import OrderSerializer, SignalSerializer, RevenueSerializer
from ..utils.constants import WEEKDAY_TRANSFORM, DATE_FORMAT, POINT_VALUE
from .line import push_message
from .shioaji import open_position, close_position
from dotenv import load_dotenv

load_dotenv()


def get_today_date_info():
    today_date = datetime.today()
    today_date_str = today_date.strftime(DATE_FORMAT)
    date_pieces = today_date_str.split("/")
    today_day = WEEKDAY_TRANSFORM[today_date.weekday()]
    return today_date_str, date_pieces, today_day


def record_deal(deal, contract_code, action):
    today_date_str, date_pieces, today_day = get_today_date_info()
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
        message = f"Order serialization failed: {serializer.errors}"
        print(message)
        push_message(message)


def record_revenue(deal, contract_code, action):
    today_date_str, date_pieces, today_day = get_today_date_info()
    cost_price = deal["cost_price"]
    price = deal["price"]
    quantity = deal["quantity"]
    direction = "Buy" if action == "Sell" else "Sell"
    diff_price = price - cost_price
    revenue = diff_price * quantity * POINT_VALUE[
        contract_code] if direction == "Buy" else -1 * diff_price * quantity * POINT_VALUE[contract_code]
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
        "diff_price": diff_price,
        "revenue": revenue
    }
    serializer = RevenueSerializer(data=revenue_data_obj)
    if serializer.is_valid():
        serializer.save()
        return revenue_data_obj
    else:
        message = f"Revenue serialization failed: {serializer.errors}"
        print(message)
        push_message(message)
        return None


def open_orders():
    try:
        latest_signal_data = Signal.objects.latest('created_at')
        serializer = SignalSerializer(latest_signal_data)
        data = dict(serializer.data)
        if data['date'] is None:
            trading_signal = data['trading_signal']
            action = {1: 'Buy', -1: 'Sell'}.get(trading_signal, None)
            contract_code = os.getenv('PRODUCT_CODE')
            quantity = int(os.getenv('PRODUCT_QUANTITY', '0'))
            if trading_signal is not None and quantity != 0:
                deal_result = open_position(contract_code, action, quantity)
                if deal_result is not None:
                    record_deal(deal_result, contract_code, action)
                else:
                    message = 'Deal is in trouble, please check your account'
                    print(message)
                    push_message(message)
            else:
                message = 'Signal is none, please check db'
                print(message)
                push_message(message)
        else:
            message = 'Not latest signal, please check db'
            print(message)
            push_message(message)
    except Exception as e:
        message = f"Place order error: {e}"
        print(message)
        push_message(message)


def close_orders():
    try:
        contract_code = os.getenv('PRODUCT_CODE')
        deal_result = close_position(contract_code)
        if deal_result is not None:
            action = deal_result['action']
            record_deal(deal_result, contract_code, action)
            revenue_data = record_revenue(deal_result, contract_code, action)
            if revenue_data is not None:
                formatted_string = (f"Today's revenue:\n\n"
                                    f"1. {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n"
                                    f"2. product: {contract_code}\n"
                                    f"3. direction: {revenue_data['direction']}\n"
                                    f"4. open_price: {revenue_data['direction']}\n"
                                    f"5. close_price: {revenue_data['open_price']}\n"
                                    f"6. revenue: {revenue_data['revenue']}\n"
                                    f"7. quantity: {revenue_data['quantity']}")
                push_message(formatted_string)
        else:
            message = 'Deal is in trouble, please check your account'
            print(message)
            push_message(message)
    except Exception as e:
        message = f"Close order error: {e}"
        print(message)
        push_message(message)
