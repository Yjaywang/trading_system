import shioaji as sj
import os
import time
from dotenv import load_dotenv
from ..models import Order
from ..serializers import OrderSerializer
from .line import push_message
from datetime import datetime, timedelta, time as dt_time

load_dotenv()

# TXF    大臺
# MXF    小臺
ca_file_name = os.getenv('SHIOAJI_CA_FILE_NAME') or ''
current_directory = os.path.dirname(__file__)
# Go up one directory level
parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
ca_file_path = os.path.join(parent_directory, ca_file_name)

api = sj.Shioaji()
accounts = api.login(os.getenv('SHIOAJI_API_KEY') or '', os.getenv('SHIOAJI_SECRET_KEY') or '')
api.activate_ca(
    ca_path=ca_file_path,
    ca_passwd=os.getenv('SHIOAJI_CA_PASSWORD') or '',
    person_id=os.getenv('SHIOAJI_PERSONAL_ID') or '',
)


def get_sell_order(quantity):
    return api.Order(
        action=sj.constant.Action.Sell,              # type: ignore
        price=0,
        quantity=quantity,
        price_type=sj.constant.FuturesPriceType.MKP, # type: ignore
        order_type=sj.constant.OrderType.IOC,        # type: ignore
        octype=sj.constant.FuturesOCType.Auto,       # type: ignore
        account=api.futopt_account)


def get_order(action, quantity):
    action = get_actio_type(action)
    if action is not None:
        return api.Order(
            action=action,
            price=0,
            quantity=quantity,
            price_type=sj.constant.FuturesPriceType.MKP, # type: ignore
            order_type=sj.constant.OrderType.IOC,        # type: ignore
            octype=sj.constant.FuturesOCType.Auto,       # type: ignore
            account=api.futopt_account)


def get_contract_type(contract_type):
    return getattr(api.Contracts.Futures, contract_type, None)


def get_actio_type(action_type):
    return getattr(sj.constant.Action, action_type, None) # type: ignore


def get_latest_contract(contract_type):
    return min([x for x in contract_type if x.code[-2:] not in ["R1", "R2"]], key=lambda x: x.delivery_date)


def make_trade(contract, order):
    if api.futopt_account is None:
        print("no futures account")
        return None
    else:
        return api.place_order(contract, order, timeout=0)


def record_deal(prodcut, quantity, action, deal_price):
    data = {'prodcut': prodcut, 'quantity': quantity, 'action': action, 'deal_price': deal_price}
    serializer = OrderSerializer(data=data)
    if serializer.is_valid():
        serializer.save()


def make_deal(contract_code, action, quantity): # Buy, Sell
    try:
        contract_type = get_contract_type(contract_code)
        contract = get_latest_contract(contract_type)
        order = get_order(action, quantity)
        trade = make_trade(contract, order)
        if trade is not None:
            time.sleep(3)
            api.update_status(trade=trade)

            dict_trade = dict(trade)                                                       # type: ignore
            status = dict_trade['status']['status']
            deals = dict_trade['status']['deals']
            total_deal_price = 0
            total_deal_quantity = 0
            avg_deal_price = 0
            if status == 'Filled':
                for deal in deals:
                    total_deal_price += int(deal['price'] * deal['quantity'])
                    total_deal_quantity += deal['quantity']
                avg_deal_price = total_deal_price / total_deal_quantity
                record_deal(contract_code, quantity, action, avg_deal_price)
                formatted_string = (f"Make a good deal\n\n"
                                    f"1. {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n"
                                    f"2. product:{contract_code}\n"
                                    f"3. price:{avg_deal_price}\n"
                                    f"4. quantity:{total_deal_quantity}")
                push_message(formatted_string)
            else:
                push_message('Trade is not Filled.')
    except Exception as e:
        print(f"make deal error: {e}")
        push_message(f"Make deal error: {e}")