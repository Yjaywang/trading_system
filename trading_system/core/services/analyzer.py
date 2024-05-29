import pandas as pd
import os
from ..models import OptionData, PriceData, Signal, Settlement
from ..serializers import OptionDataSerializer, PriceDataSerializer, SignalSerializer, SettlementSerializer
from ..utils.trding_signal import trading_signal_v1, reverse_signal_v1, settlement_signal_v1
from datetime import datetime, timedelta, time as dt_time
from .line import push_message


def run_analysis():
    is_db_no_data = True
    try:
        latest_signal_data = Signal.objects.latest('created_at')
        is_db_no_data = False
        if latest_signal_data.date is not None:
            print('no latest signal')
            return
        latest_date_str = latest_signal_data.ref_date
        latest_date = datetime.strptime(latest_date_str, "%Y/%m/%d")
        start_date = latest_date + timedelta(days=1)
    except Signal.DoesNotExist:
        print("No SingalData found in the database.")
        latest_date_str = datetime.today().strftime("%Y/%m/%d")
        latest_date = datetime.strptime(latest_date_str, "%Y/%m/%d")
        start_date = latest_date
    try:
        end_date = datetime.today()
        current_date = start_date
        while current_date <= end_date:
            formatted_target_day = current_date.strftime("%Y/%m/%d")
            print(formatted_target_day)

            option_data = OptionData.objects.filter(date=formatted_target_day)
            option_serializer = OptionDataSerializer(option_data, many=True)
            reverse_signal = reverse_signal_v1(formatted_target_day)
            settlement_signal = settlement_signal_v1(formatted_target_day)

            if len(option_serializer.data) > 0:
                data = option_serializer.data[0]
                call_count = data['call_count']
                call_amount = data['call_amount']
                put_count = data['put_count']
                put_amount = data['put_amount']

                # update previous signal
                if not is_db_no_data:
                    latest_signal_data = Signal.objects.latest('created_at')
                    update_signal_data_obj = {
                        'year': data['year'],
                        'month': data['month'],
                        'date': data['date'],
                        'day': data['day'],
                        'settlement_signal': 1 if settlement_signal else 0,
                    }
                    serializer = SignalSerializer(latest_signal_data, data=update_signal_data_obj, partial=True)
                    # latest_signal_data.date need to be null
                    if serializer.is_valid() and not latest_signal_data.date:
                        serializer.save()
                        print('Signal data successfully updated.')

                signal = trading_signal_v1(call_count, call_amount, put_count, put_amount)
                signal_data_obj = {
                    'ref_date': data['date'],
                    'reverse_signal': 1 if reverse_signal else 0,
                    'trading_signal': signal if not reverse_signal else signal * -1,
                }

                # search for db existing ref_date
                is_existing = Signal.objects.filter(ref_date=signal_data_obj['ref_date']).exists()
                ## insert latest signal
                if not is_existing:
                    serializer = SignalSerializer(data=signal_data_obj)
                    if serializer.is_valid():
                        serializer.save()
                        is_db_no_data = False
                        print("Signal data successfully saved.")
                    else:
                        print("Validation errors occurred.")
                        print(serializer.errors)
                        push_message(f'sync signal data validation error: {serializer.errors}')
                latest_op = OptionData.objects.filter(date__gt=formatted_target_day).order_by('date').first()
                latest_op_data_serializer = OptionDataSerializer(latest_op)
                latest_op_data = dict(latest_op_data_serializer.data)
                if current_date.date() == datetime.today().date():
                    message = (
                        f"A good analsis done for you\n\n"
                        f"1. {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n"
                        f"2. ref_date:{signal_data_obj['ref_date']}\n"
                        f"3. trading_signal:{signal_data_obj['trading_signal']}\n"
                        f"4. reverse_signal:{signal_data_obj['reverse_signal']}\n"
                        f"tw_call_count/amount: {latest_op_data['tw_trade_call_count']} / {latest_op_data['tw_trade_call_amount']}\n"
                        f"tw_put_count/amount: {latest_op_data['tw_trade_put_count']} / {latest_op_data['tw_trade_put_amount']}\n"
                        f"fr_call_count/amount: {latest_op_data['fr_trade_call_count']} / {latest_op_data['fr_trade_call_amount']}\n"
                        f"fr_put_count/amount: {latest_op_data['fr_trade_put_count']} / {latest_op_data['fr_trade_put_amount']}\n"
                        f"call_count/amount: {latest_op_data['call_count']} / {latest_op_data['call_amount']}\n"
                        f"put_count/amount: {latest_op_data['put_count']} / {latest_op_data['put_amount']}\n")
                    push_message(message)
            current_date += timedelta(days=1)
    except Exception as e:
        print(f"sync signal data error: {e}")
        push_message(f'sync signal data error: {e}')


def back_test():
    pass
