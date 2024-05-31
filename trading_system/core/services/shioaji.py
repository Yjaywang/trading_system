import shioaji as sj
import os
import time
from dotenv import load_dotenv
from .line import push_message
from datetime import datetime

load_dotenv()

# TXF    大臺
# MXF    小臺
ca_file_name = os.getenv('SHIOAJI_CA_FILE_NAME', '')
current_directory = os.path.dirname(__file__)
parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
ca_file_path = os.path.join(parent_directory, ca_file_name)


def initialize_api():
    api = sj.Shioaji(simulation=(os.getenv('APP_ENV') != 'production'))
    api.login(
        api_key=os.getenv('SHIOAJI_API_KEY', ''), secret_key=os.getenv('SHIOAJI_SECRET_KEY', ''), receive_window=60000)
    api.activate_ca(
        ca_path=ca_file_path,
        ca_passwd=os.getenv('SHIOAJI_CA_PASSWORD', ''),
        person_id=os.getenv('SHIOAJI_PERSONAL_ID', ''),
    )
    return api


def get_order(api, action, quantity):
    action = get_action_type(action)
    if action is not None:
        return api.Order(
            action=action,
            price=0,
            quantity=quantity,
            price_type=sj.constant.FuturesPriceType.MKP, # type: ignore
            order_type=sj.constant.OrderType.IOC,        # type: ignore
            octype=sj.constant.FuturesOCType.Auto,       # type: ignore
            account=api.futopt_account)


def get_contract_type(api, contract_type):
    return getattr(api.Contracts.Futures, contract_type, None)


def get_action_type(action_type):
    return getattr(sj.constant.Action, action_type, None) # type: ignore


def get_latest_contract(contract_type):
    return min([x for x in contract_type if x.code[-2:] not in ["R1", "R2"]], key=lambda x: x.delivery_date)


def make_a_deal(api, contract, order):
    if api.futopt_account is None:
        print("no futures account")
        return None
    else:
        return api.place_order(contract, order, timeout=0)


def get_current_position(api):
    return api.list_positions(account=api.futopt_account, timeout=20)


def update_trade_status(api: sj.Shioaji, trade):
    api.update_status(trade=trade)
    return dict(trade)


def process_deal(trade, contract_code, action):
    status = trade['status']['status']
    deals = trade['status']['deals']
    if status == 'Filled':
        total_deal_price = sum(int(deal['price'] * deal['quantity']) for deal in deals)
        total_deal_quantity = sum(deal['quantity'] for deal in deals)
        avg_deal_price = total_deal_price / total_deal_quantity
        formatted_string = (f"A good deal done\n\n"
                            f"1. {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n"
                            f"2. product: {contract_code}\n"
                            f"3. action: {action}\n"
                            f"4. avg_price: {avg_deal_price}\n"
                            f"5. quantity: {total_deal_quantity}")
        push_message(formatted_string)
        return {'price': avg_deal_price, 'quantity': total_deal_quantity, 'action': action}
    else:
        message = 'Trade is not Filled.'
        print(message)
        push_message(message)
        return None


def open_position(contract_code, action, quantity): # Buy, Sell
    try:
        api = initialize_api()
        contract_type = get_contract_type(api, contract_code)
        contract = get_latest_contract(contract_type)
        order = get_order(api, action, quantity)
        trade = make_a_deal(api, contract, order)
        time.sleep(30)
        if trade is not None:
            updated_trade = update_trade_status(api, trade)
            return process_deal(updated_trade, contract_code, action)
        return None
    except Exception as e:
        message = f"Open position error"
        print(message)
        push_message(message)
        return None
    finally:
        api.logout()


def close_position(contract_code):
    try:
        action = ""
        quantity = 0
        cost_price = 0
        api = initialize_api()
        contract_type = get_contract_type(api, contract_code)
        current_position = get_current_position(api)
        if not current_position:
            message = "No position in account"
            print(message)
            push_message(message)
            return None
        for position in current_position:
            data = dict(position)
            if contract_code in data['code']:
                action = {'Sell': 'Buy', 'Buy': 'Sell'}.get(data['direction'], '')
                quantity = data.get('quantity', 0)
                cost_price = data.get('price', 0)
                break
        if not action or not quantity:
            message = 'No matching position found'
            print(message)
            push_message(message)
            return None
        contract = get_latest_contract(contract_type)
        order = get_order(api, action, quantity)
        trade = make_a_deal(api, contract, order)
        if trade:
            time.sleep(30)
            updated_trade = update_trade_status(api, trade)
            deal_result = process_deal(updated_trade, contract_code, action)
            if deal_result is not None:
                deal_result['cost_price'] = cost_price
                return deal_result
        return None
    except Exception as e:
        message = f"Close position error:{e}"
        print(message)
        push_message(message)
        return None
    finally:
        api.logout()


def login_cron():
    try:
        api = initialize_api()
        current_position = get_current_position(api)
        return None
    except Exception:
        return None
    finally:
        api.logout()
