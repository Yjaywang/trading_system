import os
import time
import json
from datetime import datetime, timedelta, time as dt_time
import pandas as pd
from dotenv import load_dotenv
from ..models import OptionData, PriceData
from ..serializers import OptionDataSerializer, PriceDataSerializer
from ..utils.helper import post_form_data, parse_html

load_dotenv()


def run_op_scraper():
    try:
        # Get last option record
        latest_option_data = OptionData.objects.latest('created_at')
        serializer = OptionDataSerializer(latest_option_data)
        data = dict(serializer.data)
        latest_date_str = data.get('date', datetime.today().strftime("%Y/%m/%d"))
        latest_date = datetime.strptime(latest_date_str, "%Y/%m/%d")
        start_date = latest_date + timedelta(days=1)
    except OptionData.DoesNotExist:
        print("No OptionData found in the database.")
        latest_date_str = datetime.today().strftime("%Y/%m/%d")
        latest_date = datetime.strptime(latest_date_str, "%Y/%m/%d")
        start_date = latest_date
    try:
        end_date = datetime.today()
        op_data_objs = []
        weekday_transform = {
            0: "Mon",
            1: "Tue",
            2: "Wed",
            3: "Thu",
            4: "Fri",
            5: "Sat",
            6: "Sun",
        }

        current_date = start_date
        while current_date <= end_date:
            formatted_target_day = current_date.strftime("%Y/%m/%d")
            target_day = weekday_transform[current_date.weekday()]
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
            print(op_raw_data)
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
            # Sleep for 3 seconds before the next iteration
            time.sleep(3)
            current_date += timedelta(days=1)
        if len(op_data_objs) > 0:
            serializer = OptionDataSerializer(data=op_data_objs, many=True)
            if serializer.is_valid():
                OptionData.objects.bulk_create([OptionData(**item) for item in serializer.data])
                print("Option data successfully saved.")
            else:
                print("Validation errors occurred.")
                print(serializer.errors)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def run_price_scraper():
    is_db_no_data = True
    try:
        # get last option record
        latest_price_data = PriceData.objects.latest('created_at')
        is_db_no_data = False
        serializer = PriceDataSerializer(latest_price_data)
        data = dict(serializer.data)
        latest_date_str = data.get('date', datetime.today().strftime("%Y/%m/%d"))
        latest_date = datetime.strptime(latest_date_str, "%Y/%m/%d")
        end_date = datetime.today()

        # normally need to end in day period
        if data.get('period', 'day') == 'night' and latest_date == end_date:
            start_date = latest_date
        else:
            start_date = latest_date + timedelta(days=1)
    except PriceData.DoesNotExist:
        print("No PriceData found in the database.")
        # latest_date_str = datetime.today().strftime("%Y/%m/%d")
        latest_date_str = '2024/05/01'
        latest_date = datetime.strptime(latest_date_str, "%Y/%m/%d")
        start_date = latest_date
        end_date = datetime.today()

    try:
        # latest_date_str = '2024/05/01'

        market_data_objs = []
        weekday_transform = {
            0: "Mon",
            1: "Tue",
            2: "Wed",
            3: "Thu",
            4: "Fri",
            5: "Sat",
            6: "Sun",
        }
        market_code_transform = {'day': 0, "night": 1}
        current_date = start_date

        while current_date <= end_date:
            now_time = datetime.now()
            # Create a datetime object for today at 14:00
            today_14pm = datetime.combine(now_time.date(), dt_time(14, 0))
            market_periods = ['night', 'day']

            if current_date == latest_date and now_time < today_14pm and is_db_no_data:
                market_periods = ['night']
            if current_date == latest_date and now_time < today_14pm and not is_db_no_data:
                break
            if current_date == latest_date and now_time >= today_14pm and not is_db_no_data:
                market_periods = ['day']
            formatted_target_day = current_date.strftime("%Y/%m/%d")
            target_day = weekday_transform[current_date.weekday()]
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
            time.sleep(3)
            current_date += timedelta(days=1)
        market_df = pd.DataFrame(market_data_objs)
        print(market_df)
        if len(market_data_objs) > 0:
            serializer = PriceDataSerializer(data=market_data_objs, many=True)
            if serializer.is_valid():
                PriceData.objects.bulk_create([PriceData(**item) for item in serializer.data])
                print("Price data successfully saved.")
            else:
                print("Validation errors occurred.")
                print(serializer.errors)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def insert_settlement_date():
    with open('trading_system/core/settlement.json', 'r') as json_file:
        settlement_date = json.load(json_file)
    print(settlement_date)
