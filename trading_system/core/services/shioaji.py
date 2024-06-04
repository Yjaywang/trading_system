import shioaji as sj
import os
import time
from dotenv import load_dotenv
from .line import push_message
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed
import logging

load_dotenv()

# TXF    大臺
# MXF    小臺
ca_file_name = os.getenv('SHIOAJI_CA_FILE_NAME', '')
current_directory = os.path.dirname(__file__)
parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
ca_file_path = os.path.join(parent_directory, ca_file_name)


class ShioajiAPI:

    def __init__(self):
        self.api = sj.Shioaji(simulation=(os.getenv('APP_ENV') != 'production'))

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    def initialize_api(self):
        if self.api is not None:
            try:
                self.api.login(
                    api_key=os.getenv('SHIOAJI_API_KEY', ''),
                    secret_key=os.getenv('SHIOAJI_SECRET_KEY', ''),
                    receive_window=60000)
                self.api.activate_ca(
                    ca_path=ca_file_path,
                    ca_passwd=os.getenv('SHIOAJI_CA_PASSWORD', ''),
                    person_id=os.getenv('SHIOAJI_PERSONAL_ID', ''),
                )
            except Exception:
                logging.error(f"Error initializing api")
                raise Exception

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    def close(self):
        if self.api is not None:
            try:
                self.api.logout()
                self.api = None
            except Exception:
                logging.error(f"Error closing api")
                raise Exception

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    def usage(self):
        if self.api is not None:
            try:
                return self.api.usage()
            except Exception:
                logging.error(f"Error fetching usage")
                raise Exception

    @staticmethod
    def get_action_type(action_type):
        return getattr(sj.constant.Action, action_type, None) # type: ignore

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    def get_order(self, action, quantity):
        if self.api is not None:
            try:
                action = ShioajiAPI.get_action_type(action)
                if action is not None:
                    return self.api.Order(
                        action=action,
                        price=0,
                        quantity=quantity,
                        price_type=sj.constant.FuturesPriceType.MKP, # type: ignore
                        order_type=sj.constant.OrderType.IOC,        # type: ignore
                        octype=sj.constant.FuturesOCType.Auto,       # type: ignore
                        account=self.api.futopt_account)
            except Exception:
                logging.error(f"Error getting order")
                raise Exception

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    def get_contract_type(self, contract_type):
        if self.api is not None:
            try:
                return getattr(self.api.Contracts.Futures, contract_type, None)
            except Exception:
                logging.error(f"Error getting contract type")
                raise Exception

    def get_latest_contract(self, contract_type):
        return min([x for x in contract_type if x.code[-2:] not in ["R1", "R2"]], key=lambda x: x.delivery_date)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    def make_a_deal(self, contract, order):
        if self.api is not None:
            try:
                return self.api.place_order(contract, order, timeout=0)
            except Exception:
                logging.error(f"Error making a deal")
                raise Exception

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    def get_current_position(self):
        if self.api is not None and self.api.futopt_account:
            try:
                return self.api.list_positions(account=self.api.futopt_account, timeout=20000)
            except Exception:
                logging.error(f"Error getting positions")
                raise Exception

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
    def update_trade_status(self, trade):
        if self.api is not None:
            try:
                max_retries = 10
                retry_count = 0
                while True:
                    self.api.update_status(trade=trade)
                    updated_trade = dict(trade)
                    if updated_trade['status']['status'] == 'Filled':
                        break
                    retry_count += 1
                    if retry_count >= max_retries:
                        print("Max retries reached, exiting loop.")
                        break
                    time.sleep(5)
                return dict(trade)
            except Exception:
                logging.error(f"Error updating trade status")
                raise Exception


def process_deal(trade, contract_code, action):
    status = trade['status']['status']
    deals = trade['status']['deals']
    if status == 'Filled':
        total_deal_price = sum(deal['price'] * deal['quantity'] for deal in deals)
        total_deal_quantity = sum(deal['quantity'] for deal in deals)
        avg_deal_price = total_deal_price / total_deal_quantity
        formatted_string = (f"A good deal done\n\n"
                            f"1. {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n"
                            f"2. Product: {contract_code}\n"
                            f"3. Action: {action}\n"
                            f"4. Avg Price: {avg_deal_price}\n"
                            f"5. Quantity: {total_deal_quantity}")
        push_message(formatted_string)
        return {'price': avg_deal_price, 'quantity': total_deal_quantity, 'action': action}
    else:
        message = 'Trade is not filled.'
        print(message)
        push_message(message)
        return None


def open_position(contract_code, action, quantity): # Buy, Sell
    api_wrapper = ShioajiAPI()
    try:
        api_wrapper.initialize_api()
        contract_type = api_wrapper.get_contract_type(contract_code)
        contract = api_wrapper.get_latest_contract(contract_type)
        current_position = api_wrapper.get_current_position()
        if current_position:
            for position in current_position:
                data = dict(position)
                if contract_code in data['code']:
                    message = f"position already exists."
                    print(message)
                    push_message(message)
                    return None
        order = api_wrapper.get_order(action, quantity)
        trade = api_wrapper.make_a_deal(contract, order)
        if trade is not None:
            updated_trade = api_wrapper.update_trade_status(trade)
            return process_deal(updated_trade, contract_code, action)
        return None
    except Exception:
        message = f"Open position error"
        print(message)
        push_message(message)
        return None
    finally:
        api_wrapper.close()


def close_position(contract_code):
    api_wrapper = ShioajiAPI()
    try:
        action = ""
        quantity = 0
        cost_price = 0
        api_wrapper.initialize_api()
        contract_type = api_wrapper.get_contract_type(contract_code)
        current_position = api_wrapper.get_current_position()
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
        contract = api_wrapper.get_latest_contract(contract_type)
        order = api_wrapper.get_order(action, quantity)
        trade = api_wrapper.make_a_deal(contract, order)
        if trade:
            updated_trade = api_wrapper.update_trade_status(trade)
            deal_result = process_deal(updated_trade, contract_code, action)
            if deal_result is not None:
                deal_result['cost_price'] = cost_price
                return deal_result
        return None
    except Exception:
        message = f"Close position error"
        print(message)
        push_message(message)
        return None
    finally:
        api_wrapper.close()


def get_position():
    api_wrapper = ShioajiAPI()
    try:
        position_data_objs = []
        api_wrapper.initialize_api()
        current_position = api_wrapper.get_current_position()
        if not current_position:
            return position_data_objs
        for position in current_position:
            data = dict(position)
            position_data_objs.append(data)
        return position_data_objs
    except Exception as e:
        message = f"Get position error"
        print(message)
        push_message(message)
        return None
    finally:
        api_wrapper.close()


def get_api_usage():
    api_wrapper = ShioajiAPI()
    try:
        api_wrapper.initialize_api()
        data = api_wrapper.usage()
        return data
    except Exception:
        return None
    finally:
        api_wrapper.close()
