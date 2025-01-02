from ..models import OptionData, Signal, Revenue
from ..serializers import OptionDataSerializer, SignalSerializer, RevenueSerializer
from ..utils.trading_signal import trading_signal_v4, reverse_signal_v1, settlement_signal_v1, calculate_final_signal
from datetime import datetime, timedelta, time as dt_time, date
from .line import push_message
from ..utils.constants import DATE_FORMAT
from django.db.models import Sum
from django.db.models.functions import ExtractWeek, ExtractYear, ExtractMonth
from .shioaji import get_account_margin


def run_analysis():
    is_db_no_data = True
    try:
        latest_signal_data = Signal.objects.latest('created_at')
        is_db_no_data = False
        if latest_signal_data.date is not None:
            print('no latest signal')
            return
        latest_date_str = latest_signal_data.ref_date
        latest_date = datetime.strptime(latest_date_str, DATE_FORMAT)
        start_date = latest_date + timedelta(days=1)
    except Signal.DoesNotExist:
        print("No SingalData found in the database.")
        latest_date_str = datetime.today().strftime(DATE_FORMAT)
        latest_date = datetime.strptime(latest_date_str, DATE_FORMAT)
        start_date = latest_date
    try:
        end_date = datetime.today()
        current_date = start_date
        while current_date <= end_date:
            formatted_target_day = current_date.strftime(DATE_FORMAT)
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
                tw_trade_call_count = data['tw_trade_call_count']
                tw_trade_call_amount = data['tw_trade_call_amount']
                tw_trade_put_count = data['tw_trade_put_count']
                tw_trade_put_amount = data['tw_trade_put_amount']
                fr_trade_call_count = data['fr_trade_call_count']
                fr_trade_call_amount = data['fr_trade_call_amount']
                fr_trade_put_count = data['fr_trade_put_count']
                fr_trade_put_amount = data['fr_trade_put_amount']

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

                overall_signal = trading_signal_v4(call_count, call_amount, put_count, put_amount)
                tw_signal = trading_signal_v4(tw_trade_call_count,
                                              tw_trade_call_amount,
                                              tw_trade_put_count,
                                              tw_trade_put_amount)
                fr_signal = trading_signal_v4(fr_trade_call_count,
                                              fr_trade_call_amount,
                                              fr_trade_put_count,
                                              fr_trade_put_amount)
                signals = {
                    "overall_signal": overall_signal,
                    "tw_signal": tw_signal,
                    "fr_signal": fr_signal,
                    "reverse_signal": reverse_signal,
                    'settlement_signal': 1 if settlement_signal else 0,
                    'option_data': data
                }
                final_signal = calculate_final_signal(signals)
                signal_data_obj = {
                    'ref_date': data['date'],
                    "tw_trading_signal": tw_signal,
                    "fr_trading_signal": fr_signal,
                    "overall_trading_signal": overall_signal,
                    'reverse_signal': 1 if reverse_signal else 0,
                    'trading_signal': final_signal
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

                if current_date.date() == datetime.today().date():
                    latest_op = OptionData.objects.latest('created_at')
                    latest_op_data_serializer = OptionDataSerializer(latest_op)
                    latest_op_data = dict(latest_op_data_serializer.data)
                    message = (f"A good analsis done for you\n\n"
                               f"1. {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n"
                               f"2. ref_date:{signal_data_obj['ref_date']}\n"
                               f"3. trading_signal:{signal_data_obj['trading_signal']}\n"
                               f"4. tw_trading_signal:{signal_data_obj['tw_trading_signal']}\n"
                               f"5. fr_trading_signal:{signal_data_obj['fr_trading_signal']}\n"
                               f"6. reverse_signal:{signal_data_obj['reverse_signal']}\n"
                               f"tw_call_count/amount:\n"
                               f"{latest_op_data['tw_trade_call_count']} / {latest_op_data['tw_trade_call_amount']}\n"
                               f"tw_put_count/amount:\n"
                               f"{latest_op_data['tw_trade_put_count']} / {latest_op_data['tw_trade_put_amount']}\n"
                               f"fr_call_count/amount:\n"
                               f"{latest_op_data['fr_trade_call_count']} / {latest_op_data['fr_trade_call_amount']}\n"
                               f"fr_put_count/amount:\n"
                               f"{latest_op_data['fr_trade_put_count']} / {latest_op_data['fr_trade_put_amount']}\n"
                               f"call_count/amount:\n"
                               f"{latest_op_data['call_count']} / {latest_op_data['call_amount']}\n"
                               f"put_count/amount:\n"
                               f"{latest_op_data['put_count']} / {latest_op_data['put_amount']}")
                    push_message(message)
            current_date += timedelta(days=1)
    except Exception as e:
        print(f"sync signal data error: {e}")
        push_message(f'sync signal data error: {e}')


def _get_current_weekday_dates():
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday()) # get Monday
    end_of_week = start_of_week + timedelta(days=4)     # get Friday
    return start_of_week.strftime(DATE_FORMAT), end_of_week.strftime(DATE_FORMAT)


def _get_current_month_dates(year, month):
    start_of_month = date(year, month, 1)
    if month == 12:
        end_of_month = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_of_month = date(year, month + 1, 1) - timedelta(days=1)
    start_of_month_str = start_of_month.strftime(DATE_FORMAT)
    end_of_month_str = end_of_month.strftime(DATE_FORMAT)
    return start_of_month_str, end_of_month_str


def get_revenue(time_filter):
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    current_week = now.isocalendar()[1]

    if time_filter == 'week':
        start_date, end_date = _get_current_weekday_dates()
    elif time_filter == 'month':
        start_date, end_date = _get_current_month_dates(current_year, current_month)
    elif time_filter == 'year':
        start_date = date(current_year, 1, 1)
        end_date = date(current_year, 12, 31)
    else:
        raise ValueError("Invalid time filter. Choose from 'week', 'month', 'year'.")

    if time_filter == 'week':
        current_revenue = (
            Revenue.objects.filter(created_at__year=current_year).annotate(week_num=ExtractWeek('created_at')).filter(
                week_num=current_week).aggregate(total_revenue=Sum('revenue'), total_gain_price=Sum('gain_price')))
    elif time_filter == 'month':
        current_revenue = (
            Revenue.objects.filter(created_at__year=current_year).annotate(month_num=ExtractMonth('created_at')).filter(
                month_num=current_month).aggregate(total_revenue=Sum('revenue'), total_gain_price=Sum('gain_price')))
    elif time_filter == 'year':
        current_revenue = (
            Revenue.objects.filter(created_at__year=current_year).aggregate(
                total_revenue=Sum('revenue'), total_gain_price=Sum('gain_price')))

    # Construct the data object
    data_obj = {
        'current_year': current_year,
        'current_month': current_month,
        'current_week': current_week,
        'start_date': start_date,
        'end_date': end_date,
        'total_gain_price': current_revenue['total_gain_price'],
        'total_revenue': current_revenue['total_revenue']
    }
    return data_obj


def _get_this_week_revenue():
    return get_revenue('week')


def _get_this_month_revenue():
    return get_revenue('month')


def _get_this_year_revenue():
    return get_revenue('year')


def send_this_week_results():
    data = _get_this_week_revenue()
    message = (f"{data['current_year']} week {data['current_week']} result:\n\n"
               f"From: {data['start_date']}\n"
               f"To: {data['end_date']}\n"
               f"1. Gain price: {data['total_gain_price']}\n"
               f"2. Revenue: {data['total_revenue']}")
    push_message(message)


def send_this_month_results():
    data = _get_this_month_revenue()
    message = (f"{data['current_year']}/{data['current_month']} result:\n\n"
               f"From: {data['start_date']}\n"
               f"To: {data['end_date']}\n"
               f"1. Gain price: {data['total_gain_price']}\n"
               f"2. Revenue: {data['total_revenue']}")
    push_message(message)


def send_this_year_results():
    data = _get_this_year_revenue()
    message = (f"{data['current_year']} result:\n\n"
               f"From: {data['start_date']}\n"
               f"To: {data['end_date']}\n"
               f"1. Gain price: {data['total_gain_price']}\n"
               f"2. Revenue: {data['total_revenue']}")
    push_message(message)


def get_risk_condition():
    data = get_account_margin()
    if data is not None:
        margin_dict = dict(data)
        initial_margin = margin_dict['initial_margin']
        equity_amount = margin_dict['equity_amount']
        available_margin = margin_dict['available_margin']
        print(initial_margin != 0)
        if initial_margin != 0:
            if available_margin <= 0:
                message = (f"!!!Warning!!!\n\n"
                           f"available_margin: {available_margin}\n"
                           f"less than 0")
                push_message(message)
            if equity_amount / initial_margin < 1.7:
                message = (f"!!!Warning!!!\n\n"
                           f"margin ratio: {round(equity_amount / initial_margin,2)}\n"
                           f"less than 1.7")
                push_message(message)


def back_test():
    pass
