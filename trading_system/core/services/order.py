import os
from datetime import datetime
from ..models import Signal, Order
from ..serializers import OrderSerializer, SignalSerializer
from ..utils.constants import WEEKDAY_TRANSFORM, DATE_FORMAT
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


def place_orders():
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
        else:
            message = 'Deal is in trouble, please check your account'
            print(message)
            push_message(message)
    except Exception as e:
        message = f"Close order error: {e}"
        print(message)
        push_message(message)
