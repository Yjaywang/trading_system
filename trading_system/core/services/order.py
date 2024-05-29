import os
import requests
from ..models import Signal, Order
from ..serializers import OrderSerializer, PriceDataSerializer, SignalSerializer, SettlementSerializer
from datetime import datetime, timedelta, time as dt_time
from .line import push_message
from .shioaji import make_deal
from dotenv import load_dotenv

load_dotenv()


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
                deal_result = make_deal(contract_code, action, quantity)
                if deal_result is not None:
                    weekday_transform = {
                        0: "Mon",
                        1: "Tue",
                        2: "Wed",
                        3: "Thu",
                        4: "Fri",
                        5: "Sat",
                        6: "Sun",
                    }
                    today_date = datetime.today()
                    today_date_str = today_date.strftime("%Y/%m/%d")
                    date_pieces = today_date_str.split('/')
                    today_day = weekday_transform[today_date.weekday()]

                    order_data_obj = {
                        'year': date_pieces[0],
                        'month': date_pieces[1],
                        'date': today_date_str,
                        'day': today_day,
                        'prodcut': contract_code,
                        'quantity': deal_result['quantity'],
                        'action': action,
                        'deal_price': deal_result['price'],
                    }
                    serializer = OrderSerializer(data=order_data_obj)
                    if serializer.is_valid():
                        serializer.save()
                else:
                    print('Deal is in trouble, please check your account')
                    push_message('Deal is in trouble, please check your account')
            else:
                print('Signal is none, please check db')
                push_message('Signal is none, please check db')
        else:
            print('Not latest signal, please check db')
            push_message('Not latest signal, please check db')
    except Exception as e:
        print(f"Make order error: {e}")
        push_message(f"Make order error: {e}")


def close_orders():
    pass
