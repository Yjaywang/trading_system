import requests
from ..models import Signal, Order
from ..serializers import OptionDataSerializer, PriceDataSerializer, SignalSerializer, SettlementSerializer
from .line import push_message


def place_orders():
    latest_signal_data = Signal.objects.latest('created_at')
    serializer = SignalSerializer(latest_signal_data)
    data = dict(serializer.data)
    if not data['date']:
        trading_signal = data['trading_signal']
        action = {1: 'buy', -1: 'sell'}.get(trading_signal, 'stay')
        order_data_obj = {
            'year': 11,
            'month': 11,
            'date': 11,
            'day': 11,
            'prodcut': 11,
            'quantity': 11,
            'action': 11,
            'deal_price': 11,
        }

    push_message(f'1. date: 2024/05/27\n2. action: {action} \n3. status: success')


def close_orders():
    pass
