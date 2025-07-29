from core.models import OptionData, Signal, Revenue, UnfulfilledFt, UnfulfilledOp
from core.serializers import (
    OptionDataSerializer,
    SignalSerializer,
    UnfulfilledFtSerializer,
    UnfulfilledOpSerializer,
)
from core.utils.trading_signal import (
    trading_signal_v4,
    trading_signal_v5,
    reverse_signal_v1,
    settlement_signal_v1,
    calculate_final_signal,
)
from datetime import datetime, timedelta, time as date
from core.lib.line import push_bubble_message, push_message
from core.utils.constants import DATE_FORMAT, EMOJI_MAP, TRADING_SIGNAL_MAP
from core.utils.trump_words import (
    TRUMP_STYLE_ANALYSIS_JOKES,
    TRUMP_STYLE_TRADING_CONGRATS,
    TRUMP_STYLE_LOSS_COMFORTS,
    TRUMP_STYLE_MARGIN_CALL_JOKES,
)
from django.db.models import Sum
from django.db.models.functions import ExtractWeek, ExtractMonth
from core.lib.shioaji import get_account_margin
from core.types import BubbleMessage
import random
from core.middleware.error_decorators import core_logger
from core.services.scraper import get_fear_greed_index, run_report_scraper
from core.lib.gemini import analyze_trading_report
from core.utils.prompt import SYSTEM_PROMPTS
from django.core.cache import cache
from django.conf import settings


def run_analysis():
    is_db_no_data = True
    try:
        latest_signal_data = Signal.objects.latest("created_at")
        is_db_no_data = False
        if latest_signal_data.date is not None:
            core_logger.info("no latest signal")
            return
        latest_date_str = latest_signal_data.ref_date
        latest_date = datetime.strptime(latest_date_str, DATE_FORMAT)
        start_date = latest_date + timedelta(days=1)
    except Signal.DoesNotExist:
        core_logger.info("No SignalData found in the database.")
        latest_date_str = datetime.today().strftime(DATE_FORMAT)
        latest_date = datetime.strptime(latest_date_str, DATE_FORMAT)
        start_date = latest_date
    try:
        end_date = datetime.today()
        current_date = start_date
        while current_date <= end_date:
            formatted_target_day = current_date.strftime(DATE_FORMAT)
            core_logger.info(formatted_target_day)

            option_data = OptionData.objects.filter(date=formatted_target_day)
            option_serializer = OptionDataSerializer(option_data, many=True)
            reverse_signal = reverse_signal_v1(formatted_target_day)
            settlement_signal = settlement_signal_v1(formatted_target_day)

            if len(option_serializer.data) > 0:
                data = option_serializer.data[0]
                call_count = data["call_count"]
                call_amount = data["call_amount"]
                put_count = data["put_count"]
                put_amount = data["put_amount"]
                tw_trade_call_count = data["tw_trade_call_count"]
                tw_trade_call_amount = data["tw_trade_call_amount"]
                tw_trade_put_count = data["tw_trade_put_count"]
                tw_trade_put_amount = data["tw_trade_put_amount"]
                fr_trade_call_count = data["fr_trade_call_count"]
                fr_trade_call_amount = data["fr_trade_call_amount"]
                fr_trade_put_count = data["fr_trade_put_count"]
                fr_trade_put_amount = data["fr_trade_put_amount"]

                # update previous signal
                if not is_db_no_data:
                    latest_signal_data = Signal.objects.latest("created_at")
                    update_signal_data_obj = {
                        "year": data["year"],
                        "month": data["month"],
                        "date": data["date"],
                        "day": data["day"],
                        "settlement_signal": 1 if settlement_signal else 0,
                    }
                    serializer = SignalSerializer(
                        latest_signal_data, data=update_signal_data_obj, partial=True
                    )
                    # latest_signal_data.date need to be null
                    if serializer.is_valid() and not latest_signal_data.date:
                        serializer.save()
                        core_logger.info("Signal data successfully updated.")

                overall_signal = trading_signal_v4(
                    call_count, call_amount, put_count, put_amount
                )
                tw_signal = trading_signal_v4(
                    tw_trade_call_count,
                    tw_trade_call_amount,
                    tw_trade_put_count,
                    tw_trade_put_amount,
                )
                fr_signal = trading_signal_v4(
                    fr_trade_call_count,
                    fr_trade_call_amount,
                    fr_trade_put_count,
                    fr_trade_put_amount,
                )
                signals = {
                    "overall_signal": overall_signal,
                    "tw_signal": tw_signal,
                    "fr_signal": fr_signal,
                    "reverse_signal": reverse_signal,
                    "settlement_signal": 1 if settlement_signal else 0,
                    "option_data": data,
                }
                final_signal = calculate_final_signal(signals)
                signal_data_obj = {
                    "ref_date": data["date"],
                    "tw_trading_signal": tw_signal,
                    "fr_trading_signal": fr_signal,
                    "overall_trading_signal": overall_signal,
                    "reverse_signal": 1 if reverse_signal else 0,
                    "trading_signal": final_signal,
                }

                # search for db existing ref_date
                is_existing = Signal.objects.filter(
                    ref_date=signal_data_obj["ref_date"]
                ).exists()
                ## insert latest signal
                if not is_existing:
                    serializer = SignalSerializer(data=signal_data_obj)
                    if serializer.is_valid():
                        serializer.save()
                        is_db_no_data = False
                        core_logger.info("Signal data successfully saved.")
                    else:
                        core_logger.error(
                            f"Validation errors occurred. {serializer.errors}"
                        )

                if current_date.date() == datetime.today().date():
                    latest_op = OptionData.objects.latest("created_at")
                    latest_op_data_serializer = OptionDataSerializer(latest_op)
                    latest_op_data = dict(latest_op_data_serializer.data)
                    bubble_message: BubbleMessage = {
                        "header": f"Today's analysis for you",
                        "body": [
                            f"1. {datetime.now().strftime('%Y/%m/%d')}",
                            f"2. ref_date:{signal_data_obj['ref_date']}",
                            f"3. trading_signal:{TRADING_SIGNAL_MAP[signal_data_obj['trading_signal']]}",
                            f"4. tw_trading_signal:{TRADING_SIGNAL_MAP[signal_data_obj['tw_trading_signal']]}",
                            f"5. fr_trading_signal:{TRADING_SIGNAL_MAP[signal_data_obj['fr_trading_signal']]}",
                            f"6. reverse_signal:{EMOJI_MAP['success'] if signal_data_obj['reverse_signal']==1 else EMOJI_MAP['failure']}",
                            f"tw_call_count/amount:",
                            f"tw_put_count/amount:",
                            f"{latest_op_data['tw_trade_call_count']} / {latest_op_data['tw_trade_call_amount']}",
                            f"{latest_op_data['tw_trade_put_count']} / {latest_op_data['tw_trade_put_amount']}",
                            f"---",
                            f"fr_call_count/amount:",
                            f"fr_put_count/amount:",
                            f"{latest_op_data['fr_trade_call_count']} / {latest_op_data['fr_trade_call_amount']}",
                            f"{latest_op_data['fr_trade_put_count']} / {latest_op_data['fr_trade_put_amount']}",
                            f"---",
                            f"call_count/amount:",
                            f"put_count/amount:",
                            f"{latest_op_data['call_count']} / {latest_op_data['call_amount']}",
                            f"{latest_op_data['put_count']} / {latest_op_data['put_amount']}",
                            f"---",
                            f"{random.choice(TRUMP_STYLE_ANALYSIS_JOKES)}",
                            f"---",
                        ],
                        "footer": f"Suggest to do: {TRADING_SIGNAL_MAP[signal_data_obj['trading_signal']]}",
                    }
                    push_bubble_message(bubble_message)
            current_date += timedelta(days=1)
    except Exception as e:
        core_logger.error(f"sync signal data error: {e}")


def run_analysis_v2():
    is_db_no_data = True
    try:
        latest_signal_data = Signal.objects.latest("created_at")
        is_db_no_data = False
        if latest_signal_data.date is not None:
            core_logger.info("no latest signal")
            return
        latest_date_str = latest_signal_data.ref_date
        latest_date = datetime.strptime(latest_date_str, DATE_FORMAT)
        start_date = latest_date + timedelta(days=1)
    except Signal.DoesNotExist:
        core_logger.info("No SignalData found in the database.")
        latest_date_str = datetime.today().strftime(DATE_FORMAT)
        latest_date = datetime.strptime(latest_date_str, DATE_FORMAT)
        start_date = latest_date
    try:
        end_date = datetime.today()
        current_date = start_date
        while current_date <= end_date:
            formatted_target_day = current_date.strftime(DATE_FORMAT)
            core_logger.info(formatted_target_day)

            option_data = OptionData.objects.filter(date=formatted_target_day)
            option_serializer = OptionDataSerializer(option_data, many=True)
            reverse_signal = reverse_signal_v1(formatted_target_day)
            settlement_signal = settlement_signal_v1(formatted_target_day)

            if len(option_serializer.data) > 0:
                data = option_serializer.data[0]
                call_count = data["call_count"]
                call_amount = data["call_amount"]
                put_count = data["put_count"]
                put_amount = data["put_amount"]
                tw_trade_call_count = data["tw_trade_call_count"]
                tw_trade_call_amount = data["tw_trade_call_amount"]
                tw_trade_put_count = data["tw_trade_put_count"]
                tw_trade_put_amount = data["tw_trade_put_amount"]
                fr_trade_call_count = data["fr_trade_call_count"]
                fr_trade_call_amount = data["fr_trade_call_amount"]
                fr_trade_put_count = data["fr_trade_put_count"]
                fr_trade_put_amount = data["fr_trade_put_amount"]

                # update previous signal
                if not is_db_no_data:
                    latest_signal_data = Signal.objects.latest("created_at")
                    update_signal_data_obj = {
                        "year": data["year"],
                        "month": data["month"],
                        "date": data["date"],
                        "day": data["day"],
                        "settlement_signal": 1 if settlement_signal else 0,
                    }
                    serializer = SignalSerializer(
                        latest_signal_data, data=update_signal_data_obj, partial=True
                    )
                    # latest_signal_data.date need to be null
                    if serializer.is_valid() and not latest_signal_data.date:
                        serializer.save()
                        core_logger.info("Signal data successfully updated.")

                overall_signal = trading_signal_v5(
                    call_count, call_amount, put_count, put_amount, data["day"]
                )
                tw_signal = trading_signal_v5(
                    tw_trade_call_count,
                    tw_trade_call_amount,
                    tw_trade_put_count,
                    tw_trade_put_amount,
                    data["day"],
                )
                fr_signal = trading_signal_v5(
                    fr_trade_call_count,
                    fr_trade_call_amount,
                    fr_trade_put_count,
                    fr_trade_put_amount,
                    data["day"],
                )

                signal_data_obj = {
                    "ref_date": data["date"],
                    "tw_trading_signal": tw_signal,
                    "fr_trading_signal": fr_signal,
                    "overall_trading_signal": overall_signal,
                    "reverse_signal": 1 if reverse_signal else 0,
                    "trading_signal": overall_signal,
                }

                # search for db existing ref_date
                is_existing = Signal.objects.filter(
                    ref_date=signal_data_obj["ref_date"]
                ).exists()
                ## insert latest signal
                if not is_existing:
                    serializer = SignalSerializer(data=signal_data_obj)
                    if serializer.is_valid():
                        serializer.save()
                        is_db_no_data = False
                        core_logger.info("Signal data successfully saved.")
                    else:
                        core_logger.error(
                            f"Validation errors occurred. {serializer.errors}"
                        )

                if current_date.date() == datetime.today().date():
                    latest_op = OptionData.objects.latest("created_at")
                    latest_op_data_serializer = OptionDataSerializer(latest_op)
                    latest_op_data = dict(latest_op_data_serializer.data)
                    bubble_message: BubbleMessage = {
                        "header": f"Today's analysis for you",
                        "body": [
                            f"1. {datetime.now().strftime('%Y/%m/%d')}",
                            f"2. ref_date:{signal_data_obj['ref_date']}",
                            f"3. trading_signal:{TRADING_SIGNAL_MAP[signal_data_obj['trading_signal']]}",
                            f"4. tw_trading_signal:{TRADING_SIGNAL_MAP[signal_data_obj['tw_trading_signal']]}",
                            f"5. fr_trading_signal:{TRADING_SIGNAL_MAP[signal_data_obj['fr_trading_signal']]}",
                            f"6. reverse_signal:{EMOJI_MAP['success'] if signal_data_obj['reverse_signal']==1 else EMOJI_MAP['failure']}",
                            f"tw_call_count/amount:",
                            f"tw_put_count/amount:",
                            f"{latest_op_data['tw_trade_call_count']} / {latest_op_data['tw_trade_call_amount']}",
                            f"{latest_op_data['tw_trade_put_count']} / {latest_op_data['tw_trade_put_amount']}",
                            f"---",
                            f"fr_call_count/amount:",
                            f"fr_put_count/amount:",
                            f"{latest_op_data['fr_trade_call_count']} / {latest_op_data['fr_trade_call_amount']}",
                            f"{latest_op_data['fr_trade_put_count']} / {latest_op_data['fr_trade_put_amount']}",
                            f"---",
                            f"call_count/amount:",
                            f"put_count/amount:",
                            f"{latest_op_data['call_count']} / {latest_op_data['call_amount']}",
                            f"{latest_op_data['put_count']} / {latest_op_data['put_amount']}",
                            f"---",
                            f"{random.choice(TRUMP_STYLE_ANALYSIS_JOKES)}",
                            f"---",
                        ],
                        "footer": f"Suggest to do: {TRADING_SIGNAL_MAP[signal_data_obj['trading_signal']]}",
                    }
                    push_bubble_message(bubble_message)
            current_date += timedelta(days=1)
    except Exception as e:
        core_logger.error(f"sync signal data error: {e}")


def _get_current_weekday_dates():
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())  # get Monday
    end_of_week = start_of_week + timedelta(days=4)  # get Friday
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

    if time_filter == "week":
        start_date, end_date = _get_current_weekday_dates()
    elif time_filter == "month":
        start_date, end_date = _get_current_month_dates(current_year, current_month)
    elif time_filter == "year":
        start_date = date(current_year, 1, 1)
        end_date = date(current_year, 12, 31)
    else:
        raise ValueError("Invalid time filter. Choose from 'week', 'month', 'year'.")

    if time_filter == "week":
        current_revenue = (
            Revenue.objects.filter(created_at__year=current_year)
            .annotate(week_num=ExtractWeek("created_at"))
            .filter(week_num=current_week)
            .aggregate(total_revenue=Sum("revenue"), total_gain_price=Sum("gain_price"))
        )
    elif time_filter == "month":
        current_revenue = (
            Revenue.objects.filter(created_at__year=current_year)
            .annotate(month_num=ExtractMonth("created_at"))
            .filter(month_num=current_month)
            .aggregate(total_revenue=Sum("revenue"), total_gain_price=Sum("gain_price"))
        )
    elif time_filter == "year":
        current_revenue = Revenue.objects.filter(
            created_at__year=current_year
        ).aggregate(total_revenue=Sum("revenue"), total_gain_price=Sum("gain_price"))

    # Construct the data object
    data_obj = {
        "current_year": current_year,
        "current_month": current_month,
        "current_week": current_week,
        "start_date": start_date,
        "end_date": end_date,
        "total_gain_price": current_revenue["total_gain_price"],
        "total_revenue": current_revenue["total_revenue"],
    }
    return data_obj


def _get_this_week_revenue():
    return get_revenue("week")


def _get_this_month_revenue():
    return get_revenue("month")


def _get_this_year_revenue():
    return get_revenue("year")


def send_this_week_results():
    data = _get_this_week_revenue()
    bubble_message: BubbleMessage = {
        "header": f"{data['current_year']} week {data['current_week']} result",
        "body": [
            f"From: {data['start_date']}",
            f"To: {data['end_date']}",
            f"1. Gain price: {data['total_gain_price']}",
            f"2. Revenue: {data['total_revenue']}",
        ],
        "footer": (
            f"{EMOJI_MAP['up_chart']}{EMOJI_MAP['profit']} {random.choice(TRUMP_STYLE_TRADING_CONGRATS)}"
            if data["total_revenue"] >= 0
            else f"{EMOJI_MAP['down_chart']}{EMOJI_MAP['loss']} {random.choice(TRUMP_STYLE_LOSS_COMFORTS)}"
        ),
    }
    push_bubble_message(bubble_message)


def send_this_month_results():
    data = _get_this_month_revenue()
    bubble_message: BubbleMessage = {
        "header": f"{data['current_year']}/{data['current_month']} result",
        "body": [
            f"From: {data['start_date']}",
            f"To: {data['end_date']}",
            f"1. Gain price: {data['total_gain_price']}",
            f"2. Revenue: {data['total_revenue']}",
        ],
        "footer": (
            f"{EMOJI_MAP['up_chart']}{EMOJI_MAP['profit']} {random.choice(TRUMP_STYLE_TRADING_CONGRATS)}"
            if data["total_revenue"] >= 0
            else f"{EMOJI_MAP['down_chart']}{EMOJI_MAP['loss']} {random.choice(TRUMP_STYLE_LOSS_COMFORTS)}"
        ),
    }
    push_bubble_message(bubble_message)


def send_this_year_results():
    data = _get_this_year_revenue()
    bubble_message: BubbleMessage = {
        "header": f"{data['current_year']} result",
        "body": [
            f"From: {data['start_date']}",
            f"To: {data['end_date']}",
            f"1. Gain price: {data['total_gain_price']}",
            f"2. Revenue: {data['total_revenue']}",
        ],
        "footer": (
            f"{EMOJI_MAP['up_chart']}{EMOJI_MAP['profit']} {random.choice(TRUMP_STYLE_TRADING_CONGRATS)}"
            if data["total_revenue"] >= 0
            else f"{EMOJI_MAP['down_chart']}{EMOJI_MAP['loss']} {random.choice(TRUMP_STYLE_LOSS_COMFORTS)}"
        ),
    }
    push_bubble_message(bubble_message)


def get_risk_condition():
    data = get_account_margin()
    if data is not None:
        margin_dict = dict(data)
        initial_margin = margin_dict["initial_margin"]
        equity_amount = margin_dict["equity_amount"]
        available_margin = margin_dict["available_margin"]
        if initial_margin != 0:
            if available_margin <= 0:
                bubble_message: BubbleMessage = {
                    "header": "!!!Warning!!!",
                    "body": [
                        f"1. available_margin: {available_margin}",
                        f"2. initial_margin: {initial_margin}",
                        f"3. equity_amount: {equity_amount}",
                    ],
                    "footer": random.choice(TRUMP_STYLE_MARGIN_CALL_JOKES),
                }
                push_bubble_message(bubble_message)
            if equity_amount / initial_margin < 1.7:
                bubble_message: BubbleMessage = {
                    "header": "!!!Warning!!!",
                    "body": [
                        f"1. equity_amount: {equity_amount}",
                        f"2. initial_margin: {initial_margin}",
                        f"3. margin ratio: {round(equity_amount / initial_margin, 2)}",
                    ],
                    "footer": random.choice(TRUMP_STYLE_MARGIN_CALL_JOKES),
                }
                push_bubble_message(bubble_message)
    # push sj error message
    sj_error_messages = cache.get("sj_error")
    if sj_error_messages:
        message = "\n\n".join(sj_error_messages)
        push_message(message)
        cache.delete("sj_error")


def _get_unfulfilled_ft_data(today: date, trader_list: list):
    future_data = UnfulfilledFt.objects.filter(date=today)
    ft_analysis_list = ["TX", "MTX", "SF", "subtotal"]
    # Example: {"TX": {"fi": 0, "dt": 0}, ...}
    ft_results = {
        ft_name: {trader: 0 for trader in trader_list} for ft_name in ft_analysis_list
    }
    for future in future_data:
        ft_data = UnfulfilledFtSerializer(future).data
        if (
            ft_data["trader"] in trader_list
            and ft_data["future_name"] in ft_analysis_list
        ):
            ft_results[ft_data["future_name"]][ft_data["trader"]] = ft_data[
                "unfulfilled_count"
            ]

    return ft_results


def _get_unfulfilled_op_data(today: date, trader_list: list):
    op_data = UnfulfilledOp.objects.filter(date=today)
    print(today, op_data)
    op_analysis_list = ["call", "put"]
    direction_list = ["buy", "sell"]
    # Example: {"buy": {"call": {"fi": 0, "dt": 0}, "put": {"fi": 0, "dt": 0}}, ...}
    op_results = {
        direction: {
            op_type: {trade: 0 for trade in trader_list} for op_type in op_analysis_list
        }
        for direction in direction_list
    }
    for op in op_data:
        op_data = UnfulfilledOpSerializer(op).data
        if op_data["trader"] in trader_list and op_data["op_type"] in op_analysis_list:
            op_results[op_data["direction"]][op_data["op_type"]][op_data["trader"]] = (
                op_data["unfulfilled_count"]
            )
    return op_results


def get_unfulfilled_data():
    today = datetime.now().date()
    analysis_trader_list = ["fi", "dt"]
    # desc no duplicate dates
    distinct_dates = (
        UnfulfilledFt.objects.order_by("-date")
        .values_list("date", flat=True)
        .distinct()
    )
    previous_date = distinct_dates[1]
    today_ft_results = _get_unfulfilled_ft_data(today, analysis_trader_list)
    previous_ft_results = _get_unfulfilled_ft_data(previous_date, analysis_trader_list)
    today_op_results = _get_unfulfilled_op_data(today, analysis_trader_list)
    previous_op_results = _get_unfulfilled_op_data(previous_date, analysis_trader_list)
    delta_ft_results = {}
    delta_op_results = {}
    if (
        today_ft_results
        and previous_ft_results
        and today_op_results
        and previous_op_results
    ):

        for ft_name in today_ft_results:
            delta_ft_results[ft_name] = {
                trader: today_ft_results[ft_name][trader]
                - previous_ft_results[ft_name][trader]
                for trader in analysis_trader_list
            }
        for op_direction in today_op_results:
            delta_op_results[op_direction] = {
                op_type: {
                    trader: today_op_results[op_direction][op_type][trader]
                    - previous_op_results[op_direction][op_type][trader]
                    for trader in analysis_trader_list
                }
                for op_type in today_op_results[op_direction]
            }
    bubble_message: BubbleMessage = {
        "header": "Unfulfilled data summary",
        "body": [
            f"{datetime.now().strftime('%Y/%m/%d')}",
            f"---",
            f"Future unfulfilled data",
            f"1. TX",
            f"fr: {EMOJI_MAP['up_chart'] if delta_ft_results['TX']['fi']>=0 else EMOJI_MAP['down_chart']} {today_ft_results['TX']['fi']} ({delta_ft_results['TX']['fi']})",
            f"dt: {EMOJI_MAP['up_chart'] if delta_ft_results['TX']['dt']>=0 else EMOJI_MAP['down_chart']} {today_ft_results['TX']['dt']} ({delta_ft_results['TX']['dt']})",
            f"2. MTX",
            f"fr: {EMOJI_MAP['up_chart'] if delta_ft_results['MTX']['fi']>=0 else EMOJI_MAP['down_chart']} {today_ft_results['MTX']['fi']} ({delta_ft_results['MTX']['fi']})",
            f"dt: {EMOJI_MAP['up_chart'] if delta_ft_results['MTX']['dt']>=0 else EMOJI_MAP['down_chart']} {today_ft_results['MTX']['dt']} ({delta_ft_results['MTX']['dt']})",
            f"3. SF",
            f"fr: {EMOJI_MAP['up_chart'] if delta_ft_results['SF']['fi']>=0 else EMOJI_MAP['down_chart']} {today_ft_results['SF']['fi']} ({delta_ft_results['SF']['fi']})",
            f"dt: {EMOJI_MAP['up_chart'] if delta_ft_results['SF']['dt']>=0 else EMOJI_MAP['down_chart']} {today_ft_results['SF']['dt']} ({delta_ft_results['SF']['dt']})",
            f"4. subtotal",
            f"fr: {EMOJI_MAP['up_chart'] if delta_ft_results['subtotal']['fi']>=0 else EMOJI_MAP['down_chart']} {today_ft_results['subtotal']['fi']} ({delta_ft_results['subtotal']['fi']})",
            f"dt: {EMOJI_MAP['up_chart'] if delta_ft_results['subtotal']['dt']>=0 else EMOJI_MAP['down_chart']} {today_ft_results['subtotal']['dt']} ({delta_ft_results['subtotal']['dt']})",
            f"---",
            f"Option unfulfilled data",
            f"1. buy call",
            f"fi: {EMOJI_MAP['up_chart'] if delta_op_results['buy']['call']['fi']>=0 else EMOJI_MAP['down_chart']} {today_op_results['buy']['call']['fi']} ({delta_op_results['buy']['call']['fi']})",
            f"dt: {EMOJI_MAP['up_chart'] if delta_op_results['buy']['call']['dt']>=0 else EMOJI_MAP['down_chart']} {today_op_results['buy']['call']['dt']} ({delta_op_results['buy']['call']['dt']})",
            f"2. sell put",
            f"fi: {EMOJI_MAP['up_chart'] if delta_op_results['sell']['put']['fi']>=0 else EMOJI_MAP['down_chart']} {today_op_results['sell']['put']['fi']} ({delta_op_results['sell']['put']['fi']})",
            f"dt: {EMOJI_MAP['up_chart'] if delta_op_results['sell']['put']['dt']>=0 else EMOJI_MAP['down_chart']} {today_op_results['sell']['put']['dt']} ({delta_op_results['sell']['put']['dt']})",
            f"3. buy put",
            f"fi: {EMOJI_MAP['up_chart'] if delta_op_results['buy']['put']['fi']>=0 else EMOJI_MAP['down_chart']} {today_op_results['buy']['put']['fi']} ({delta_op_results['buy']['put']['fi']})",
            f"dt: {EMOJI_MAP['up_chart'] if delta_op_results['buy']['put']['dt']>=0 else EMOJI_MAP['down_chart']} {today_op_results['buy']['put']['dt']} ({delta_op_results['buy']['put']['dt']})",
            f"4. sell call",
            f"fi: {EMOJI_MAP['up_chart'] if delta_op_results['sell']['call']['fi']>=0 else EMOJI_MAP['down_chart']} {today_op_results['sell']['call']['fi']} ({delta_op_results['sell']['call']['fi']})",
            f"dt: {EMOJI_MAP['up_chart'] if delta_op_results['sell']['call']['dt']>=0 else EMOJI_MAP['down_chart']} {today_op_results['sell']['call']['dt']} ({delta_op_results['sell']['call']['dt']})",
            f"5. buy side",
            f"fi: {EMOJI_MAP['bull'] if today_op_results['buy']['call']['fi'] >= today_op_results['buy']['put']['fi'] else EMOJI_MAP['bear']}",
            f"dt: {EMOJI_MAP['bull'] if today_op_results['buy']['call']['dt'] >= today_op_results['buy']['put']['dt'] else EMOJI_MAP['bear']}",
            f"6. sell side",
            f"fi: {EMOJI_MAP['bull'] if today_op_results['sell']['call']['fi'] < today_op_results['sell']['put']['fi'] else EMOJI_MAP['bear']}",
            f"dt: {EMOJI_MAP['bull'] if today_op_results['sell']['call']['dt'] < today_op_results['sell']['put']['dt'] else EMOJI_MAP['bear']}",
        ],
        "footer": f"{random.choice(TRUMP_STYLE_ANALYSIS_JOKES)}",
    }
    push_bubble_message(bubble_message)


def run_pre_report_analysis():
    source_url = settings.PRE_REPORT_URL
    target_report_name = settings.PRE_REPORT_NAME
    report_pdf_url, report_pdf_date = run_report_scraper(target_report_name, source_url)
    score, rating, date, previous_1_week = get_fear_greed_index()
    if report_pdf_url:
        results = analyze_trading_report(
            report_pdf_url, SYSTEM_PROMPTS["pre_trading_analyst"]
        )
        bubble_message: BubbleMessage = {
            "header": f"{report_pdf_date}_{target_report_name}",
            "body": [
                f"Fear and Greed Index",
                f"Date: {date}",
                f"Score: {EMOJI_MAP['up_chart'] if score-previous_1_week >= 0 else EMOJI_MAP['down_chart']} {round(score,2)} ({round(score-previous_1_week,2)})",
                f"Rating: {rating}",
                f"Previous 1 Week: {round(score-previous_1_week,2)}",
                f"---",
                f"Report pdf url",
                f"{report_pdf_url}",
                f"---",
                f"Future results",
                f"TW: {results['future']['domestic']}",
                f"FR: {results['future']['foreign']}",
                f"---",
                f"Option results",
                f"TW: {results['option']['domestic']}",
                f"FR: {results['option']['foreign']}",
                f"---",
                f"Overall results",
                f"{results['overall']}",
            ],
            "footer": f"{random.choice(TRUMP_STYLE_ANALYSIS_JOKES)}",
        }
        push_bubble_message(bubble_message)
    else:
        core_logger.error("Failed to run pre-trading report analysis.")


def run_post_report_analysis():
    source_url = settings.POST_REPORT_URL
    target_report_name = settings.POST_REPORT_NAME
    report_pdf_url, report_pdf_date = run_report_scraper(target_report_name, source_url)
    if report_pdf_url:
        results = analyze_trading_report(
            report_pdf_url, SYSTEM_PROMPTS["post_trading_analyst"]
        )
        bubble_message: BubbleMessage = {
            "header": f"{report_pdf_date}_{target_report_name}",
            "body": [
                f"Report pdf url",
                f"{report_pdf_url}",
                f"---",
                f"Future results",
                f"TW: {results['future']['domestic']}",
                f"FR: {results['future']['foreign']}",
                f"Top 10: {results['future']['top_ten']}",
                f"---",
                f"Option results",
                f"TW: {results['option']['domestic']}",
                f"FR: {results['option']['foreign']}",
                f"Top 10: {results['option']['top_ten']}",
                f"---",
                f"Overall results",
                f"{results['overall']}",
            ],
            "footer": f"{random.choice(TRUMP_STYLE_ANALYSIS_JOKES)}",
        }
        push_bubble_message(bubble_message)
    else:
        core_logger.error("Failed to run post-trading report analysis.")
