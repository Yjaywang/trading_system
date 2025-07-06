import shioaji as sj
import os
import time
from dotenv import load_dotenv
from .line import push_message, push_bubble_message
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed
from ..utils.trump_words import TRUMP_STYLE_FUNNY_TRADE_BLESSINGS
from ..types import BubbleMessage
import random
from ..middleware.error_decorators import core_logger

load_dotenv()

# TXF    大臺
# MXF    小臺
ca_file_name = os.getenv("SHIOAJI_CA_FILE_NAME", "")
current_directory = os.path.dirname(__file__)
parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
ca_file_path = os.path.join(parent_directory, ca_file_name)
retry_wait_seconds = 10
retry_attempt_count = 3


class ShioajiAPI:

    def __init__(self):
        self.api = sj.Shioaji(simulation=(os.getenv("APP_ENV") != "production"))

    @retry(
        stop=stop_after_attempt(retry_attempt_count),
        wait=wait_fixed(retry_wait_seconds),
        reraise=True,
    )
    def _initialize_api(self):
        if self.api is not None:
            try:
                self.api.login(
                    api_key=os.getenv("SHIOAJI_API_KEY", ""),
                    secret_key=os.getenv("SHIOAJI_SECRET_KEY", ""),
                    receive_window=60000,
                )
                self.api.activate_ca(
                    ca_path=ca_file_path,
                    ca_passwd=os.getenv("SHIOAJI_CA_PASSWORD", ""),
                    person_id=os.getenv("SHIOAJI_PERSONAL_ID", ""),
                )
            except Exception:
                self.api.logout()
                self.api = None
                core_logger.error(f"Error initializing api")
                raise Exception

    @retry(
        stop=stop_after_attempt(retry_attempt_count),
        wait=wait_fixed(retry_wait_seconds),
        reraise=True,
    )
    def _close(self):
        if self.api is not None:
            try:
                self.api.logout()
                self.api = None
            except Exception:
                core_logger.error(f"Error closing api")
                raise Exception

    @retry(
        stop=stop_after_attempt(retry_attempt_count),
        wait=wait_fixed(retry_wait_seconds),
        reraise=True,
    )
    def _usage(self):
        if self.api is not None:
            try:
                return self.api.usage()
            except Exception:
                core_logger.error(f"Error fetching usage")
                raise Exception

    @staticmethod
    def _get_action_type(action_type):
        return getattr(sj.constant.Action, action_type, None)  # type: ignore

    @retry(
        stop=stop_after_attempt(retry_attempt_count),
        wait=wait_fixed(retry_wait_seconds),
        reraise=True,
    )
    def _get_order(self, action, quantity):
        if self.api is not None:
            try:
                action = ShioajiAPI._get_action_type(action)
                if action is not None:
                    return self.api.Order(
                        action=action,
                        price=0,
                        quantity=quantity,
                        price_type=sj.constant.FuturesPriceType.MKP,  # type: ignore
                        order_type=sj.constant.OrderType.IOC,  # type: ignore
                        octype=sj.constant.FuturesOCType.Auto,  # type: ignore
                        account=self.api.futopt_account,
                    )
            except Exception:
                core_logger.error(f"Error getting order")
                raise Exception

    @retry(
        stop=stop_after_attempt(retry_attempt_count),
        wait=wait_fixed(retry_wait_seconds),
        reraise=True,
    )
    def _get_contract_type(self, contract_type):
        if self.api is not None:
            try:
                return getattr(self.api.Contracts.Futures, contract_type, None)
            except Exception:
                core_logger.error(f"Error getting contract type")
                raise Exception

    @staticmethod
    def _get_latest_contract(contract_type):
        """For open position use"""
        today = datetime.now().strftime("%Y/%m/%d")
        today_date = datetime.strptime(today, "%Y/%m/%d")

        return min(
            [
                x
                for x in contract_type
                if x.code[-2:] not in ["R1", "R2"]
                and datetime.strptime(x.delivery_date, "%Y/%m/%d") > today_date
            ],
            key=lambda x: datetime.strptime(x.delivery_date, "%Y/%m/%d"),
        )

    @staticmethod
    def _get_contract_by_code(contract_type, contract_code):
        """For close position use"""
        return min(
            [
                x
                for x in contract_type
                if x.code[-2:] not in ["R1", "R2"] and x.code == contract_code
            ],
            key=lambda x: x.delivery_date,
        )

    @retry(
        stop=stop_after_attempt(retry_attempt_count),
        wait=wait_fixed(retry_wait_seconds),
        reraise=True,
    )
    def _make_a_deal(self, contract, order):
        if self.api is not None:
            try:
                return self.api.place_order(contract, order, timeout=0)
            except Exception:
                core_logger.error(f"Error making a deal")
                raise Exception

    @retry(
        stop=stop_after_attempt(retry_attempt_count),
        wait=wait_fixed(retry_wait_seconds),
        reraise=True,
    )
    def _get_current_position(self):
        if self.api is not None and self.api.futopt_account:
            try:
                return self.api.list_positions(
                    account=self.api.futopt_account, timeout=20000
                )
            except Exception:
                core_logger.error(f"Error getting positions")
                raise Exception

    @retry(
        stop=stop_after_attempt(retry_attempt_count),
        wait=wait_fixed(retry_wait_seconds),
        reraise=True,
    )
    def _get_current_margin(self):
        if self.api is not None and self.api.futopt_account:
            try:
                return self.api.margin(account=self.api.futopt_account, timeout=20000)
            except Exception:
                core_logger.error(f"Error getting margin")
                raise Exception

    @retry(
        stop=stop_after_attempt(retry_attempt_count),
        wait=wait_fixed(retry_wait_seconds),
        reraise=True,
    )
    def _update_trade_status(self, trade):
        if self.api is not None:
            try:
                max_retries = 10
                retry_count = 0
                while True:
                    self.api.update_status(trade=trade)
                    updated_trade = dict(trade)
                    if updated_trade["status"]["status"] == "Filled":
                        break
                    retry_count += 1
                    if retry_count >= max_retries:
                        print("Max retries reached, exiting loop.")
                        break
                    time.sleep(5)
                return dict(trade)
            except Exception:
                core_logger.error(f"Error updating trade status")
                raise Exception


def _process_deal(trade, contract_category, action):
    status = trade["status"]["status"]
    deals = trade["status"]["deals"]
    if status == "Filled":
        total_deal_price = sum(deal["price"] * deal["quantity"] for deal in deals)
        total_deal_quantity = sum(deal["quantity"] for deal in deals)
        avg_deal_price = total_deal_price / total_deal_quantity
        bubble_message: BubbleMessage = {
            "header": f" Deal start",
            "body": (
                f"1. {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n"
                f"2. Product: {contract_category}\n"
                f"3. Action: {action}\n"
                f"4. Avg Price: {avg_deal_price}\n"
                f"5. Quantity: {total_deal_quantity}"
            ),
            "footer": f"{random.choice(TRUMP_STYLE_FUNNY_TRADE_BLESSINGS)}",
        }
        push_bubble_message(bubble_message)
        return {
            "price": avg_deal_price,
            "quantity": total_deal_quantity,
            "action": action,
        }
    else:
        message = "Trade is not filled."
        print(message)
        push_message(message)
        return None


def _settlement_deal(positions, contract_category, action):
    for position in positions:
        data = dict(position)
        avg_deal_price = data["last_price"]
        total_deal_quantity = data["quantity"]
        cost_price = data["price"]
        bubble_message: BubbleMessage = {
            "header": f" Deal end",
            "body": (
                f"1. {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n"
                f"2. Product: {contract_category}\n"
                f"3. Action: {action}\n"
                f"4. Avg Price: {avg_deal_price}\n"
                f"5. Quantity: {total_deal_quantity}"
            ),
            "footer": f"{random.choice(TRUMP_STYLE_FUNNY_TRADE_BLESSINGS)}",
        }
        push_bubble_message(bubble_message)
        return {
            "price": avg_deal_price,
            "quantity": total_deal_quantity,
            "action": action,
            "cost_price": cost_price,
        }


def open_position(contract_category, action, quantity):  # Buy, Sell
    api_wrapper = ShioajiAPI()
    try:
        api_wrapper._initialize_api()
        contract_type = api_wrapper._get_contract_type(contract_category)
        contract = api_wrapper._get_latest_contract(contract_type)
        current_position = api_wrapper._get_current_position()
        if current_position:
            for position in current_position:
                data = dict(position)
                if contract_category in data["code"]:
                    message = f"position already exists."
                    print(message)
                    push_message(message)
                    return None
        order = api_wrapper._get_order(action, quantity)
        trade = api_wrapper._make_a_deal(contract, order)
        if trade is not None:
            updated_trade = api_wrapper._update_trade_status(trade)
            return _process_deal(updated_trade, contract_category, action)
        return None
    except Exception:
        message = f"Open position error"
        print(message)
        push_message(message)
        return None
    finally:
        api_wrapper._close()


def close_position(contract_category):
    api_wrapper = ShioajiAPI()
    try:
        action = ""
        quantity = 0
        cost_price = 0
        contract_code = ""
        api_wrapper._initialize_api()
        contract_type = api_wrapper._get_contract_type(contract_category)
        current_position = api_wrapper._get_current_position()
        if not current_position:
            message = "No position in account"
            print(message)
            push_message(message)
            return None

        for position in current_position:
            data = dict(position)
            if contract_category in data["code"]:
                action = {"Sell": "Buy", "Buy": "Sell"}.get(data["direction"], "")
                quantity = data.get("quantity", 0)
                cost_price = data.get("price", 0)
                contract_code = data.get("code", "")
                break
        if not action or not quantity:
            message = "No matching position found"
            print(message)
            push_message(message)
            return None

        contract = api_wrapper._get_contract_by_code(contract_type, contract_code)
        delivery_date = contract.delivery_date
        today = datetime.today().strftime("%Y/%m/%d")
        if delivery_date == today:
            message = "Settlement date will close position automatically."
            push_message(message)
            return _settlement_deal(current_position, contract_category, action)

        order = api_wrapper._get_order(action, quantity)
        trade = api_wrapper._make_a_deal(contract, order)
        if trade:
            updated_trade = api_wrapper._update_trade_status(trade)
            deal_result = _process_deal(updated_trade, contract_category, action)
            if deal_result is not None:
                deal_result["cost_price"] = cost_price
                return deal_result
        return None
    except Exception:
        message = f"Close position error"
        print(message)
        push_message(message)
        return None
    finally:
        api_wrapper._close()


def get_position():
    api_wrapper = ShioajiAPI()
    try:
        position_data_objs = []
        api_wrapper._initialize_api()
        current_position = api_wrapper._get_current_position()
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
        api_wrapper._close()


def get_api_usage():
    api_wrapper = ShioajiAPI()
    try:
        api_wrapper._initialize_api()
        data = api_wrapper._usage()
        return data
    except Exception:
        return None
    finally:
        api_wrapper._close()


def get_account_margin():
    api_wrapper = ShioajiAPI()
    try:
        api_wrapper._initialize_api()
        data = api_wrapper._get_current_margin()
        return data
    except Exception:
        return None
    finally:
        api_wrapper._close()


def close_some_position(contract_category, quantity):
    api_wrapper = ShioajiAPI()
    try:
        action = ""
        current_quantity = 0
        cost_price = 0
        contract_code = ""
        api_wrapper._initialize_api()
        contract_type = api_wrapper._get_contract_type(contract_category)
        current_position = api_wrapper._get_current_position()
        if not current_position:
            message = "No position in account"
            print(message)
            push_message(message)
            return None

        for position in current_position:
            data = dict(position)
            if contract_category in data["code"]:
                action = {"Sell": "Buy", "Buy": "Sell"}.get(data["direction"], "")
                current_quantity = data.get("quantity", 0)
                cost_price = data.get("price", 0)
                contract_code = data.get("code", "")
                break
        if quantity > current_quantity:
            message = "Exceed current position quantity"
            print(message)
            push_message(message)
            return None
        if not action:
            message = "No matching position found"
            print(message)
            push_message(message)
            return None

        contract = api_wrapper._get_contract_by_code(contract_type, contract_code)
        delivery_date = contract.delivery_date
        today = datetime.today().strftime("%Y/%m/%d")
        if delivery_date == today:
            message = "Settlement date will close position automatically."
            push_message(message)
            return _settlement_deal(current_position, contract_category, action)

        order = api_wrapper._get_order(action, quantity)
        trade = api_wrapper._make_a_deal(contract, order)
        if trade:
            updated_trade = api_wrapper._update_trade_status(trade)
            deal_result = _process_deal(updated_trade, contract_category, action)
            if deal_result is not None:
                deal_result["cost_price"] = cost_price
                return deal_result
        return None
    except Exception:
        message = f"Close position error"
        print(message)
        push_message(message)
        return None
    finally:
        api_wrapper._close()
