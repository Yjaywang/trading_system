import requests
from bs4 import BeautifulSoup
from ..models import OptionData, DayPrice, NightPrice
from ..serializers import OptionDataSerializer, DayPriceSerializer, NightPriceSerializer
from datetime import datetime, timedelta
import time
import pandas as pd
import json
import os
from dotenv import load_dotenv

load_dotenv()


def post_form_data(url, form_data):
    try:
        response = requests.post(url, data=form_data)
        if 'application/json' in response.headers.get('Content-Type', ''):
            return response.json()
        else:
            return response
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return {}


def parse_html(response):
    if 'text/html' in response.headers.get('Content-Type', ''):
        soup = BeautifulSoup(response.text, 'html.parser')
        tbody = soup.find('tbody')
        if tbody and not isinstance(tbody, str):
            rows = tbody.find_all('tr')
            table_data = []
            for row in rows:
                # Extract text from each td in the row
                cols = [td.get_text(strip=True) for td in row.find_all('td')]
                table_data.append(cols)
            return table_data
        else:
            return "No tbody found in the HTML."
    else:
        return "The response is not HTML."


def run_op_scraper() :
    try:
        # get last option record
        latest_option_data = OptionData.objects.latest('created_at')
        serializer = OptionDataSerializer(latest_option_data)
        data = dict(serializer.data)
        latest_date_str = data.get('date', datetime.today().strftime("%Y/%m/%d"))
        latest_date = datetime.strptime(latest_date_str, "%Y/%m/%d")
        start_date = latest_date + timedelta(days=1)
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

            op_url = f'{os.getenv('OPTION_DATA_API')}'
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

            if isinstance(op_raw_data, list) and  len(op_raw_data) > 0:
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

        serializer = OptionDataSerializer(data=op_data_objs, many=True)
        if serializer.is_valid():
            OptionData.objects.bulk_create([OptionData(**item) for item in serializer.data])
            print("Option data successfully saved.")
        else:
            print("Validation errors occurred.")
            print(serializer.errors)
        return (serializer.data)
    except OptionData.DoesNotExist:
        print("No OptionData found in the database.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

