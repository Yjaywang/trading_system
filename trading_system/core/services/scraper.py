import os
import time
import json
from datetime import datetime, timedelta, time as dt_time
import pandas as pd
from dotenv import load_dotenv
from ..utils.constants import WEEKDAY_TRANSFORM, DATE_FORMAT, SLEEP_DURATION, DATE_FORMAT_2
from ..models import OptionData, PriceData, Settlement, UnfulfilledOp, UnfulfilledFt
from ..serializers import OptionDataSerializer, PriceDataSerializer, SettlementSerializer, UnfulfilledOpSerializer, UnfulfilledFtSerializer
from ..utils.helper import post_form_data, parse_html
from .line import push_message

load_dotenv()


def run_op_scraper():
    try:
        # Get last option record
        latest_option_data = OptionData.objects.latest('created_at')
        serializer = OptionDataSerializer(latest_option_data)
        data = dict(serializer.data)
        latest_date_str = data.get('date', datetime.today().strftime(DATE_FORMAT))
        latest_date = datetime.strptime(latest_date_str, DATE_FORMAT)
        start_date = latest_date + timedelta(days=1)
    except OptionData.DoesNotExist:
        print("No OptionData found in the database.")
        latest_date_str = datetime.today().strftime(DATE_FORMAT)
        latest_date = datetime.strptime(latest_date_str, DATE_FORMAT)
        start_date = latest_date
    try:
        end_date = datetime.today()
        op_data_objs = []
        current_date = start_date
        while current_date <= end_date:
            formatted_target_day = current_date.strftime(DATE_FORMAT)
            target_day = WEEKDAY_TRANSFORM[current_date.weekday()]
            print(formatted_target_day)

            op_url = f"{os.getenv('OPTION_DATA_API')}"
            form_data = {
                'queryType': '1',
                'goDay': '',
                'doQuery': '1',
                'dateaddcnt': '',
                'queryDate': formatted_target_day,
                'commodityId': '',
                'button3': '送出查詢'
            }
            op_result = post_form_data(op_url, form_data)
            op_raw_data = parse_html(op_result)
            if isinstance(op_raw_data, list) and len(op_raw_data) > 0:
                tw_trade_call_count = int(op_raw_data[0][8].replace(",", ""))
                tw_trade_call_amount = int(op_raw_data[0][9].replace(",", ""))
                fr_trade_call_count = int(op_raw_data[2][5].replace(",", ""))
                fr_trade_call_amount = int(op_raw_data[2][6].replace(",", ""))
                tw_trade_put_count = int(op_raw_data[3][6].replace(",", ""))
                tw_trade_put_amount = int(op_raw_data[3][7].replace(",", ""))
                fr_trade_put_count = int(op_raw_data[5][5].replace(",", ""))
                fr_trade_put_amount = int(op_raw_data[5][6].replace(",", ""))
                op_data_obj = {
                    "year": formatted_target_day.split('/')[0],
                    "month": formatted_target_day.split('/')[1],
                    "date": formatted_target_day,
                    "day": target_day,
                    "tw_trade_call_count": tw_trade_call_count,
                    "tw_trade_call_amount": tw_trade_call_amount,
                    "fr_trade_call_count": fr_trade_call_count,
                    "fr_trade_call_amount": fr_trade_call_amount,
                    "tw_trade_put_count": tw_trade_put_count,
                    "tw_trade_put_amount": tw_trade_put_amount,
                    "fr_trade_put_count": fr_trade_put_count,
                    "fr_trade_put_amount": fr_trade_put_amount,
                    "call_count": tw_trade_call_count + fr_trade_call_count,
                    "call_amount": tw_trade_call_amount + fr_trade_call_amount,
                    "put_count": tw_trade_put_count + fr_trade_put_count,
                    "put_amount": tw_trade_put_amount + fr_trade_put_amount
                }
                op_data_objs.append(op_data_obj)
            time.sleep(SLEEP_DURATION)
            current_date += timedelta(days=1)
        if len(op_data_objs) > 0:
            # search for db existing date -> ['date1','date2'...]
            existing_data = OptionData.objects.filter(date__in=[item['date'] for item in op_data_objs]).values_list(
                'date', flat=True)
            # transform a existing set
            existing_set = set(existing_data)
            # filter new data
            new_data = [item for item in op_data_objs if item['date'] not in existing_set]
            if not new_data:
                print('sync option data already exist in db')
                return
            serializer = OptionDataSerializer(data=new_data, many=True)
            if serializer.is_valid():
                OptionData.objects.bulk_create([OptionData(**item) for item in serializer.data])
                print("Option data successfully saved.")
            else:
                print(f'sync option data validation error: {serializer.errors}')
    except Exception as e:
        print(f"sync option data error: {e}")


def run_price_scraper():
    try:
        # get last option record
        latest_price_data = PriceData.objects.latest('created_at')
        serializer = PriceDataSerializer(latest_price_data)
        data = dict(serializer.data)
        latest_date_str = data.get('date', datetime.today().strftime(DATE_FORMAT))
        latest_date = datetime.strptime(latest_date_str, DATE_FORMAT)
        end_date = datetime.today()
        # normally need to end in day period
        if data.get('period', 'day') == 'night':
            start_date = latest_date
        else:
            start_date = latest_date + timedelta(days=1)
    except PriceData.DoesNotExist:
        print("No PriceData found in the database.")
        latest_date_str = datetime.today().strftime(DATE_FORMAT)
        latest_date = datetime.strptime(latest_date_str, DATE_FORMAT)
        start_date = latest_date
        end_date = datetime.today()
    try:
        market_data_objs = []
        market_code_transform = {'day': 0, "night": 1}
        current_date = start_date
        while current_date.date() <= end_date.date():
            now_time = datetime.now()
            # Create a datetime object for today at 14:00
            today_14pm = datetime.combine(now_time.date(), dt_time(14, 0))
            market_periods = ['night', 'day']
            if current_date.date() == end_date.date() and now_time < today_14pm:
                market_periods = ['night']
            formatted_target_day = current_date.strftime(DATE_FORMAT)
            target_day = WEEKDAY_TRANSFORM[current_date.weekday()]
            market_url = f"{os.getenv('MARKET_PRICE_DATA_API')}"
            print(formatted_target_day)

            for market_period in market_periods:
                form_data = {
                    'queryType': 2,
                    'marketCode': market_code_transform[market_period],
                    'dateaddcnt': '',
                    'commodity_id': 'TX',
                    'commodity_id2': '',
                    'queryDate': formatted_target_day,
                    'MarketCode': market_code_transform[market_period],
                    'commodity_idt': 'TX',
                    'commodity_id2t': '',
                    'commodity_id2t2': '',
                }
                market_result = post_form_data(market_url, form_data)
                market_raw_data = parse_html(market_result)

                if isinstance(market_raw_data, list) and len(market_raw_data) > 0:
                    night_volume = market_raw_data[0][8] if market_raw_data[0][8] != '-' else '0'
                    day_volume = market_raw_data[0][9] if market_raw_data[0][9] != '-' else '0'
                    market_data_obj = {
                        "year": formatted_target_day.split('/')[0],
                        "month": formatted_target_day.split('/')[1],
                        "date": formatted_target_day,
                        "day": target_day,
                        'period': market_period,
                        'open': int(market_raw_data[0][2]),
                        'high': int(market_raw_data[0][3]),
                        'low': int(market_raw_data[0][4]),
                        'close': int(market_raw_data[0][5]),
                        'volume': int(night_volume) if market_period == 'night' else int(day_volume)
                    }
                    market_data_objs.append(market_data_obj)
            time.sleep(SLEEP_DURATION)
            current_date += timedelta(days=1)

        if len(market_data_objs) > 0:
            # search for db existing date -> [('date', 'period'), ('date', 'period'), ...]
            existing_data = PriceData.objects.filter(
                date__in=[item['date'] for item in market_data_objs],
                period__in=[item['period'] for item in market_data_objs]).values_list('date', 'period')
            # transform a existing set
            existing_set = set(existing_data)
            # filter new data
            new_data = [item for item in market_data_objs if (item['date'], item['period']) not in existing_set]
            if not new_data:
                print('sync price data already exist in db')
                return
            serializer = PriceDataSerializer(data=new_data, many=True)
            if serializer.is_valid():
                PriceData.objects.bulk_create([PriceData(**item) for item in serializer.data])
                print("Price data successfully saved.")
            else:
                print(f'sync price data validation error: {serializer.errors}')
    except Exception as e:
        print(f'sync price data error: {e}')


def run_unfulfilled_op_scraper():
    try:
        # Get last option record
        latest_option_data = UnfulfilledOp.objects.latest('created_at')
        serializer = UnfulfilledOpSerializer(latest_option_data)
        data = dict(serializer.data)
        latest_date_str = data.get('date', datetime.today().strftime(DATE_FORMAT))
        latest_date = datetime.strptime(latest_date_str, DATE_FORMAT_2)
        start_date = latest_date + timedelta(days=1)
    except UnfulfilledOp.DoesNotExist:
        print("No UnfulfilledOp found in the database.")
        latest_date_str = datetime.today().strftime(DATE_FORMAT)
        latest_date = datetime.strptime(latest_date_str, DATE_FORMAT)
        start_date = latest_date
    try:
        end_date = datetime.today()
        op_data_objs = []
        current_date = start_date
        while current_date <= end_date:
            formatted_target_day = current_date.strftime(DATE_FORMAT)
            target_day = WEEKDAY_TRANSFORM[current_date.weekday()]
            print(formatted_target_day)

            op_url = f"{os.getenv('OPTION_DATA_API')}"
            form_data = {
                'queryType': '1',
                'goDay': '',
                'doQuery': '1',
                'dateaddcnt': '',
                'queryDate': formatted_target_day,
                'commodityId': '',
                'button3': '送出查詢'
            }
            op_result = post_form_data(op_url, form_data)
            op_raw_data = parse_html(op_result)
            if isinstance(op_raw_data, list) and len(op_raw_data) > 0:
                raw_data_dict = {
                    "tw_trade_unfulfilled_buy_call_count": int(op_raw_data[0][10].replace(",", "")),
                    "tw_trade_unfulfilled_buy_call_amount": int(op_raw_data[0][11].replace(",", "")),
                    "tw_trade_unfulfilled_buy_put_count": int(op_raw_data[0][12].replace(",", "")),
                    "tw_trade_unfulfilled_buy_put_amount": int(op_raw_data[0][13].replace(",", "")),
                    "fr_trade_unfulfilled_buy_call_count": int(op_raw_data[2][7].replace(",", "")),
                    "fr_trade_unfulfilled_buy_call_amount": int(op_raw_data[2][8].replace(",", "")),
                    "fr_trade_unfulfilled_buy_put_count": int(op_raw_data[2][9].replace(",", "")),
                    "fr_trade_unfulfilled_buy_put_amount": int(op_raw_data[2][10].replace(",", "")),
                    "tw_trade_unfulfilled_sell_call_count": int(op_raw_data[3][8].replace(",", "")),
                    "tw_trade_unfulfilled_sell_call_amount": int(op_raw_data[3][9].replace(",", "")),
                    "tw_trade_unfulfilled_sell_put_count": int(op_raw_data[3][10].replace(",", "")),
                    "tw_trade_unfulfilled_sell_put_amount": int(op_raw_data[3][11].replace(",", "")),
                    "fr_trade_unfulfilled_sell_call_count": int(op_raw_data[5][7].replace(",", "")),
                    "fr_trade_unfulfilled_sell_call_amount": int(op_raw_data[5][8].replace(",", "")),
                    "fr_trade_unfulfilled_sell_put_count": int(op_raw_data[5][9].replace(",", "")),
                    "fr_trade_unfulfilled_sell_put_amount": int(op_raw_data[5][10].replace(",", "")),
                }
                op_types = ['call', 'put']
                directions = ['buy', 'sell']
                traders = ['tw', 'fr']
                trader_map = {'tw': 'dt', 'fr': 'fi'}
                for op_type in op_types:
                    for direction in directions:
                        for trader in traders:
                            op_data_obj = {}
                            op_data_obj['year'] = int(formatted_target_day.split('/')[0])
                            op_data_obj['month'] = int(formatted_target_day.split('/')[1])
                            op_data_obj['date'] = datetime.strptime(formatted_target_day, DATE_FORMAT).date()
                            op_data_obj['day'] = target_day
                            op_data_obj['op_type'] = op_type
                            op_data_obj['direction'] = direction
                            op_data_obj['trader'] = trader_map[trader]
                            op_data_obj['unfulfilled_count'] = raw_data_dict[
                                f'{trader}_trade_unfulfilled_{direction}_{op_type}_count']
                            op_data_obj['unfulfilled_amount'] = raw_data_dict[
                                f'{trader}_trade_unfulfilled_{direction}_{op_type}_amount']
                            op_data_objs.append(op_data_obj)
            time.sleep(SLEEP_DURATION)
            current_date += timedelta(days=1)
        if len(op_data_objs) > 0:
            # search for db existing date -> ['date1','date2'...]
            existing_data = UnfulfilledOp.objects.filter(date__in=[item['date'] for item in op_data_objs]).values_list(
                'date', flat=True)
            # transform a existing set
            existing_set = set(existing_data)
            # filter new data
            new_data = [item for item in op_data_objs if item['date'] not in existing_set]
            if not new_data:
                print('sync unfulfilled option data already exist in db')
                return
            serializer = UnfulfilledOpSerializer(data=new_data, many=True)
            if serializer.is_valid():
                UnfulfilledOp.objects.bulk_create([UnfulfilledOp(**item) for item in serializer.data])
                print("unfulfilled option data successfully saved.")
            else:
                print(f'sync unfulfilled option data validation error: {serializer.errors}')
    except Exception as e:
        print(f"sync unfulfilled option data error: {e}")


def run_unfulfilled_future_scraper():
    try:
        # Get last future record
        latest_future_data = UnfulfilledFt.objects.latest('created_at')
        serializer = UnfulfilledFtSerializer(latest_future_data)
        data = dict(serializer.data)
        latest_date_str = data.get('date', datetime.today().strftime(DATE_FORMAT))
        latest_date = datetime.strptime(latest_date_str, DATE_FORMAT_2)
        start_date = latest_date + timedelta(days=1)
    except UnfulfilledFt.DoesNotExist:
        print("No UnfulfilledFt found in the database.")
        latest_date_str = datetime.today().strftime(DATE_FORMAT)
        latest_date = datetime.strptime(latest_date_str, DATE_FORMAT)
        start_date = latest_date
    try:
        end_date = datetime.today()
        future_data_objs = []
        current_date = start_date
        while current_date <= end_date:
            formatted_target_day = current_date.strftime(DATE_FORMAT)
            target_day = WEEKDAY_TRANSFORM[current_date.weekday()]
            print(formatted_target_day)

            future_url = f"{os.getenv('FUTURE_DATA_API')}"
            form_data = {
                'queryType': '1',
                'goDay': '',
                'doQuery': '1',
                'dateaddcnt': '',
                'queryDate': formatted_target_day,
                'commodityId': '',
                'button3': '送出查詢'
            }
            future_result = post_form_data(future_url, form_data)
            future_raw_data = parse_html(future_result)
            if isinstance(future_raw_data, list) and len(future_raw_data) > 0:
                raw_data_dict = {}
                for index, future_data in enumerate(future_raw_data):
                    if future_data[1] == '臺股期貨':
                        raw_data_dict['tw_TX_unfulfilled_count'] = int(future_data[13].replace(",", ""))
                        raw_data_dict['tw_TX_unfulfilled_amount'] = int(future_data[14].replace(",", ""))
                        raw_data_dict['it_TX_unfulfilled_count'] = int(future_raw_data[index + 1][11].replace(",", ""))
                        raw_data_dict['it_TX_unfulfilled_amount'] = int(future_raw_data[index + 1][12].replace(",", ""))
                        raw_data_dict['fr_TX_unfulfilled_count'] = int(future_raw_data[index + 2][11].replace(",", ""))
                        raw_data_dict['fr_TX_unfulfilled_amount'] = int(future_raw_data[index + 2][12].replace(",", ""))
                    elif future_data[1] == '電子期貨':
                        raw_data_dict['tw_TE_unfulfilled_count'] = int(future_data[13].replace(",", ""))
                        raw_data_dict['tw_TE_unfulfilled_amount'] = int(future_data[14].replace(",", ""))
                        raw_data_dict['it_TE_unfulfilled_count'] = int(future_raw_data[index + 1][11].replace(",", ""))
                        raw_data_dict['it_TE_unfulfilled_amount'] = int(future_raw_data[index + 1][12].replace(",", ""))
                        raw_data_dict['fr_TE_unfulfilled_count'] = int(future_raw_data[index + 2][11].replace(",", ""))
                        raw_data_dict['fr_TE_unfulfilled_amount'] = int(future_raw_data[index + 2][12].replace(",", ""))
                    elif future_data[1] == '金融期貨':
                        raw_data_dict['tw_TF_unfulfilled_count'] = int(future_data[13].replace(",", ""))
                        raw_data_dict['tw_TF_unfulfilled_amount'] = int(future_data[14].replace(",", ""))
                        raw_data_dict['it_TF_unfulfilled_count'] = int(future_raw_data[index + 1][11].replace(",", ""))
                        raw_data_dict['it_TF_unfulfilled_amount'] = int(future_raw_data[index + 1][12].replace(",", ""))
                        raw_data_dict['fr_TF_unfulfilled_count'] = int(future_raw_data[index + 2][11].replace(",", ""))
                        raw_data_dict['fr_TF_unfulfilled_amount'] = int(future_raw_data[index + 2][12].replace(",", ""))
                    elif future_data[1] == '小型臺指期貨':
                        raw_data_dict['tw_MTX_unfulfilled_count'] = int(future_data[13].replace(",", ""))
                        raw_data_dict['tw_MTX_unfulfilled_amount'] = int(future_data[14].replace(",", ""))
                        raw_data_dict['it_MTX_unfulfilled_count'] = int(future_raw_data[index + 1][11].replace(",", ""))
                        raw_data_dict['it_MTX_unfulfilled_amount'] = int(future_raw_data[index + 1][12].replace(
                            ",", ""))
                        raw_data_dict['fr_MTX_unfulfilled_count'] = int(future_raw_data[index + 2][11].replace(",", ""))
                        raw_data_dict['fr_MTX_unfulfilled_amount'] = int(future_raw_data[index + 2][12].replace(
                            ",", ""))
                    elif future_data[1] == '股票期貨':
                        raw_data_dict['tw_SF_unfulfilled_count'] = int(future_data[13].replace(",", ""))
                        raw_data_dict['tw_SF_unfulfilled_amount'] = int(future_data[14].replace(",", ""))
                        raw_data_dict['it_SF_unfulfilled_count'] = int(future_raw_data[index + 1][11].replace(",", ""))
                        raw_data_dict['it_SF_unfulfilled_amount'] = int(future_raw_data[index + 1][12].replace(",", ""))
                        raw_data_dict['fr_SF_unfulfilled_count'] = int(future_raw_data[index + 2][11].replace(",", ""))
                        raw_data_dict['fr_SF_unfulfilled_amount'] = int(future_raw_data[index + 2][12].replace(",", ""))
                    elif future_data[1] == 'ETF期貨':
                        raw_data_dict['tw_ETF_unfulfilled_count'] = int(future_data[13].replace(",", ""))
                        raw_data_dict['tw_ETF_unfulfilled_amount'] = int(future_data[14].replace(",", ""))
                        raw_data_dict['it_ETF_unfulfilled_count'] = int(future_raw_data[index + 1][11].replace(",", ""))
                        raw_data_dict['it_ETF_unfulfilled_amount'] = int(future_raw_data[index + 1][12].replace(
                            ",", ""))
                        raw_data_dict['fr_ETF_unfulfilled_count'] = int(future_raw_data[index + 2][11].replace(",", ""))
                        raw_data_dict['fr_ETF_unfulfilled_amount'] = int(future_raw_data[index + 2][12].replace(
                            ",", ""))
                    elif future_data[0] == '期貨小計':
                        raw_data_dict['tw_subtotal_unfulfilled_count'] = int(future_data[12].replace(",", ""))
                        raw_data_dict['tw_subtotal_unfulfilled_amount'] = int(future_data[13].replace(",", ""))
                        raw_data_dict['it_subtotal_unfulfilled_count'] = int(future_raw_data[index + 1][11].replace(
                            ",", ""))
                        raw_data_dict['it_subtotal_unfulfilled_amount'] = int(future_raw_data[index + 1][12].replace(
                            ",", ""))
                        raw_data_dict['fr_subtotal_unfulfilled_count'] = int(future_raw_data[index + 2][11].replace(
                            ",", ""))
                        raw_data_dict['fr_subtotal_unfulfilled_amount'] = int(future_raw_data[index + 2][12].replace(
                            ",", ""))
                future_names = ['TX', 'TE', 'TF', 'MTX', 'SF', 'ETF', 'subtotal']
                traders = ['tw', 'it', 'fr']
                trader_map = {'tw': 'dt', 'fr': 'fi', 'it': 'it'}
                for future_name in future_names:
                    for trader in traders:
                        future_data_obj = {}
                        future_data_obj['year'] = int(formatted_target_day.split('/')[0])
                        future_data_obj['month'] = int(formatted_target_day.split('/')[1])
                        future_data_obj['date'] = datetime.strptime(formatted_target_day, DATE_FORMAT).date()
                        future_data_obj['day'] = target_day
                        future_data_obj['future_name'] = future_name
                        future_data_obj['trader'] = trader_map[trader]
                        future_data_obj['unfulfilled_count'] = raw_data_dict[
                            f'{trader}_{future_name}_unfulfilled_count']
                        future_data_obj['unfulfilled_amount'] = raw_data_dict[
                            f'{trader}_{future_name}_unfulfilled_amount']
                        future_data_objs.append(future_data_obj)
            time.sleep(SLEEP_DURATION)
            current_date += timedelta(days=1)
        if len(future_data_objs) > 0:
            # search for db existing date -> ['date1','date2'...]
            existing_data = UnfulfilledFt.objects.filter(
                date__in=[item['date'] for item in future_data_objs]).values_list(
                    'date', flat=True)
            # transform a existing set
            existing_set = set(existing_data)
            # filter new data
            new_data = [item for item in future_data_objs if item['date'] not in existing_set]
            if not new_data:
                print('sync unfulfilled future data already exist in db')
                return
            serializer = UnfulfilledFtSerializer(data=new_data, many=True)
            if serializer.is_valid():
                UnfulfilledFt.objects.bulk_create([UnfulfilledFt(**item) for item in serializer.data])
                print("unfulfilled future data successfully saved.")
            else:
                print(f'sync unfulfilled future data validation error: {serializer.errors}')
    except Exception as e:
        print(f"sync unfulfilled future data error: {e}")


def insert_settlement_date():
    current_directory = os.path.dirname(__file__)
    # Go up one directory level
    parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
    # Construct the path to the JSON file in the previous directory
    json_file_path = os.path.join(parent_directory, 'settlement.json')

    try:
        with open(json_file_path, 'r') as json_file:
            settlement_dates = json.load(json_file)
        settlement_date_objs = []
        for settlement_date in settlement_dates:
            pieces = settlement_date.split('/')
            settlement_date_obj = {
                'year': int(pieces[0]),
                'month': int(pieces[1]),
                'date': settlement_date,
                'day': WEEKDAY_TRANSFORM[datetime.strptime(settlement_date, DATE_FORMAT).weekday()]
            }
            settlement_date_objs.append(settlement_date_obj)

        if len(settlement_date_objs) > 0:
            # search for db existing date
            existing_data = Settlement.objects.filter(
                date__in=[item['date'] for item in settlement_date_objs]).values_list(
                    'date', flat=True)
            # transform a existing set
            existing_set = set(existing_data)
            # filter new data
            new_data = [item for item in settlement_date_objs if item['date'] not in existing_set]
            if not new_data:
                print(f'sync settlement already exist in db')
                return

            serializer = SettlementSerializer(data=new_data, many=True)
            if serializer.is_valid():
                Settlement.objects.bulk_create([Settlement(**item) for item in serializer.data])
                print("Settlement date successfully saved.")
            else:
                print(f'sync settlement validation error: {serializer.errors}')
    except Exception as e:
        print(f'sync settlement error: {e}')


#bulk insert from csv
def insert_init_op():
    current_directory = os.path.dirname(__file__)
    # Go up one directory level
    parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
    # Construct the path to the JSON file in the previous directory
    csv_paths = [
        os.path.join(parent_directory, 'op_2021.csv'),
        os.path.join(parent_directory, 'op_2022.csv'),
        os.path.join(parent_directory, 'op_2023.csv'),
        os.path.join(parent_directory, 'op_2024.csv'),
    ]

    option_dfs = []
    for path in csv_paths:
        df = pd.read_csv(path)
        option_dfs.append(df)

    option_raw_df = pd.concat(option_dfs, ignore_index=True)
    option_columns_to_keep = [
        'year',
        'month',
        'date',
        'day',
        'tw_trade_call_count',
        'tw_trade_call_amount',
        'fr_trade_call_count',
        'fr_trade_call_amount',
        'tw_trade_put_count',
        'tw_trade_put_amount',
        'fr_trade_put_count',
        'fr_trade_put_amount',
        'call_count',
        'call_amount',
        'put_count',
        'put_amount'
    ]
    option_df = option_raw_df[option_columns_to_keep]
    option_objs = [dict(row) for _, row in option_df.iterrows()]
    try:
        if len(option_objs) > 0:
            serializer = OptionDataSerializer(data=option_objs, many=True)
            if serializer.is_valid():
                OptionData.objects.bulk_create([OptionData(**item) for item in serializer.data])
                print("Settlement date successfully saved.")
            else:
                print("Validation errors occurred.")
                print(serializer.errors)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def insert_init_price():
    current_directory = os.path.dirname(__file__)
    # Go up one directory level
    parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
    # Construct the path to the JSON file in the previous directory
    csv_paths = [
        os.path.join(parent_directory, 'market_2021.csv'),
        os.path.join(parent_directory, 'market_2022.csv'),
        os.path.join(parent_directory, 'market_2023.csv'),
        os.path.join(parent_directory, 'market_2024.csv'),
    ]
    market_dfs = []
    for path in csv_paths:
        df = pd.read_csv(path)
        market_dfs.append(df)

    market_raw_df = pd.concat(market_dfs, ignore_index=True)
    market_columns_to_keep = [
        'year',
        'month',
        'date',
        'day',
        'd_open',
        'd_high',
        'd_low',
        'd_close',
        'n_open',
        'n_high',
        'n_low',
        'n_close',
        'd_quantity',
        'n_quantity'
    ]
    market_df = market_raw_df[market_columns_to_keep]
    price_objs = []
    for _, row in market_df.iterrows():
        data = dict(row)
        day_obj = {
            'year': data['year'],
            'month': data['month'],
            'date': data['date'],
            'day': data['day'],
            'open': data['d_open'],
            'high': data['d_high'],
            'low': data['d_low'],
            'close': data['d_close'],
            'volume': data['d_quantity'],
            'period': 'day'
        }
        night_obj = {
            'year': data['year'],
            'month': data['month'],
            'date': data['date'],
            'day': data['day'],
            'open': data['n_open'],
            'high': data['n_high'],
            'low': data['n_low'],
            'close': data['n_close'],
            'volume': data['n_quantity'],
            'period': 'night'
        }
        price_objs.append(night_obj)
        price_objs.append(day_obj)
    try:
        if len(price_objs) > 0:
            serializer = PriceDataSerializer(data=price_objs, many=True)
            if serializer.is_valid():
                PriceData.objects.bulk_create([PriceData(**item) for item in serializer.data])
                print("Settlement date successfully saved.")
            else:
                print("Validation errors occurred.")
                print(serializer.errors)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


#bulk insert from csv
def insert_init_unfulfilled_op():
    current_directory = os.path.dirname(__file__)
    # Go up one directory level
    parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
    # Construct the path to the JSON file in the previous directory
    csv_paths = [
        os.path.join(parent_directory, 'op_unfulfilled_2022.csv'),
        os.path.join(parent_directory, 'op_unfulfilled_2023.csv'),
        os.path.join(parent_directory, 'op_unfulfilled_2024.csv'),
        os.path.join(parent_directory, 'op_unfulfilled_2025.csv'),
    ]

    option_dfs = []
    for path in csv_paths:
        df = pd.read_csv(path)
        option_dfs.append(df)

    option_raw_df = pd.concat(option_dfs, ignore_index=True)
    option_columns_to_keep = [
        'year',
        'month',
        'date',
        'day',
        'tw_trade_unfulfilled_buy_call_count',
        'tw_trade_unfulfilled_buy_call_amount',
        'tw_trade_unfulfilled_buy_put_count',
        'tw_trade_unfulfilled_buy_put_amount',
        'fr_trade_unfulfilled_buy_call_count',
        'fr_trade_unfulfilled_buy_call_amount',
        'fr_trade_unfulfilled_buy_put_count',
        'fr_trade_unfulfilled_buy_put_amount',
        'tw_trade_unfulfilled_sell_call_count',
        'tw_trade_unfulfilled_sell_call_amount',
        'tw_trade_unfulfilled_sell_put_count',
        'tw_trade_unfulfilled_sell_put_amount',
        'fr_trade_unfulfilled_sell_call_count',
        'fr_trade_unfulfilled_sell_call_amount',
        'fr_trade_unfulfilled_sell_put_count',
        'fr_trade_unfulfilled_sell_put_amount',
    ]
    option_df = option_raw_df[option_columns_to_keep]
    option_objs = []
    for _, row in option_df.iterrows():
        op_types = ['call', 'put']
        directions = ['buy', 'sell']
        traders = ['tw', 'fr']
        trader_map = {'tw': 'dt', 'fr': 'fi'}
        for op_type in op_types:
            for direction in directions:
                for trader in traders:
                    data = {}
                    data['year'] = row['year']
                    data['month'] = row['month']
                    data['date'] = datetime.strptime(row['date'], DATE_FORMAT).date()
                    data['day'] = row['day']
                    data['op_type'] = op_type
                    data['direction'] = direction
                    data['trader'] = trader_map[trader]
                    data['unfulfilled_count'] = row[f'{trader}_trade_unfulfilled_{direction}_{op_type}_count']
                    data['unfulfilled_amount'] = row[f'{trader}_trade_unfulfilled_{direction}_{op_type}_amount']
                    option_objs.append(data)

    try:
        if len(option_objs) > 0:
            serializer = UnfulfilledOpSerializer(data=option_objs, many=True)
            if serializer.is_valid():
                UnfulfilledOp.objects.bulk_create([UnfulfilledOp(**item) for item in serializer.data])
                print("unfulfilled op data successfully saved.")
            else:
                print("Validation errors occurred.")
                print(serializer.errors)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def insert_init_unfulfilled_ft():
    current_directory = os.path.dirname(__file__)
    # Go up one directory level
    parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
    # Construct the path to the JSON file in the previous directory
    csv_paths = [
        os.path.join(parent_directory, 'future_unfulfilled_2022.csv'),
        os.path.join(parent_directory, 'future_unfulfilled_2023.csv'),
        os.path.join(parent_directory, 'future_unfulfilled_2024.csv'),
        os.path.join(parent_directory, 'future_unfulfilled_2025.csv'),
    ]

    future_dfs = []
    for path in csv_paths:
        df = pd.read_csv(path)
        future_dfs.append(df)

    future_raw_df = pd.concat(future_dfs, ignore_index=True)
    future_columns_to_keep = [
        "year",
        "month",
        "date",
        "day",
        "tw_TX_unfulfilled_count",
        "tw_TX_unfulfilled_amount",
        "it_TX_unfulfilled_count",
        "it_TX_unfulfilled_amount",
        "fr_TX_unfulfilled_count",
        "fr_TX_unfulfilled_amount",
        "tw_TE_unfulfilled_count",
        "tw_TE_unfulfilled_amount",
        "it_TE_unfulfilled_count",
        "it_TE_unfulfilled_amount",
        "fr_TE_unfulfilled_count",
        "fr_TE_unfulfilled_amount",
        "tw_TF_unfulfilled_count",
        "tw_TF_unfulfilled_amount",
        "it_TF_unfulfilled_count",
        "it_TF_unfulfilled_amount",
        "fr_TF_unfulfilled_count",
        "fr_TF_unfulfilled_amount",
        "tw_MTX_unfulfilled_count",
        "tw_MTX_unfulfilled_amount",
        "it_MTX_unfulfilled_count",
        "it_MTX_unfulfilled_amount",
        "fr_MTX_unfulfilled_count",
        "fr_MTX_unfulfilled_amount",
        "tw_SF_unfulfilled_count",
        "tw_SF_unfulfilled_amount",
        "it_SF_unfulfilled_count",
        "it_SF_unfulfilled_amount",
        "fr_SF_unfulfilled_count",
        "fr_SF_unfulfilled_amount",
        "tw_ETF_unfulfilled_count",
        "tw_ETF_unfulfilled_amount",
        "it_ETF_unfulfilled_count",
        "it_ETF_unfulfilled_amount",
        "fr_ETF_unfulfilled_count",
        "fr_ETF_unfulfilled_amount",
        "tw_subtotal_unfulfilled_count",
        "tw_subtotal_unfulfilled_amount",
        "it_subtotal_unfulfilled_count",
        "it_subtotal_unfulfilled_amount",
        "fr_subtotal_unfulfilled_count",
        "fr_subtotal_unfulfilled_amount"
    ]

    future_df = future_raw_df[future_columns_to_keep]
    future_objs = []
    for _, row in future_df.iterrows():
        future_names = ['TX', 'TE', 'TF', 'MTX', 'SF', 'ETF', 'subtotal']
        traders = ['tw', 'it', 'fr']
        trader_map = {'tw': 'dt', 'fr': 'fi', 'it': 'it'}
        for future_name in future_names:
            for trader in traders:
                data = {}
                data['year'] = row['year']
                data['month'] = row['month']
                data['date'] = datetime.strptime(row['date'], DATE_FORMAT).date()
                data['day'] = row['day']
                data['future_name'] = future_name
                data['trader'] = trader_map[trader]
                data['unfulfilled_count'] = row[f'{trader}_{future_name}_unfulfilled_count']
                data['unfulfilled_amount'] = row[f'{trader}_{future_name}_unfulfilled_amount']
                future_objs.append(data)

    try:
        if len(future_objs) > 0:
            serializer = UnfulfilledFtSerializer(data=future_objs, many=True)
            if serializer.is_valid():
                UnfulfilledFt.objects.bulk_create([UnfulfilledFt(**item) for item in serializer.data])
                print("unfulfilled future data successfully saved.")
            else:
                print("Validation errors occurred.")
                print(serializer.errors)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
