import os
import time
import json
from datetime import datetime, timedelta, time as dt_time
import pandas as pd
from dotenv import load_dotenv
from ..utils.constants import WEEKDAY_TRANSFORM, DATE_FORMAT, SLEEP_DURATION
from ..models import OptionData, PriceData, Settlement
from ..serializers import OptionDataSerializer, PriceDataSerializer, SettlementSerializer
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
            # transform a existiing set
            existing_set = set(existing_data)
            # filter new data
            new_data = [item for item in op_data_objs if item['date'] not in existing_set]
            if not new_data:
                message = 'sync option data already exist in db'
                print(message)
                push_message(message)
                return
            serializer = OptionDataSerializer(data=new_data, many=True)
            if serializer.is_valid():
                OptionData.objects.bulk_create([OptionData(**item) for item in serializer.data])
                print("Option data successfully saved.")
            else:
                message = f'sync option data validation error: {serializer.errors}'
                print(message)
                push_message(message)
    except Exception as e:
        message = f"sync option data error: {e}"
        print(message)
        push_message(message)


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
            # transform a existiing set
            existing_set = set(existing_data)
            # filter new data
            new_data = [item for item in market_data_objs if (item['date'], item['period']) not in existing_set]
            if not new_data:
                message = 'sync price data already exist in db'
                print(message)
                push_message(message)
                return
            serializer = PriceDataSerializer(data=new_data, many=True)
            if serializer.is_valid():
                PriceData.objects.bulk_create([PriceData(**item) for item in serializer.data])
                print("Price data successfully saved.")
            else:
                message = f'sync price data validation error: {serializer.errors}'
                print(message)
                push_message(message)
    except Exception as e:
        message = f'sync price data error: {e}'
        print(message)
        push_message(message)


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
            # transform a existiing set
            existing_set = set(existing_data)
            # filter new data
            new_data = [item for item in settlement_date_objs if item['date'] not in existing_set]
            if not new_data:
                message = f'sync settlement already exist in db'
                print(message)
                push_message(message)
                return

            serializer = SettlementSerializer(data=new_data, many=True)
            if serializer.is_valid():
                Settlement.objects.bulk_create([Settlement(**item) for item in serializer.data])
                print("Settlement date successfully saved.")
            else:
                message = f'sync settlement validation error: {serializer.errors}'
                print(message)
                push_message(message)
    except Exception as e:
        message = f'sync settlement error: {e}'
        print(message)
        push_message(message)


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
