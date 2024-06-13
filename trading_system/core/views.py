from .utils.decorators import require_secret_token
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .services.scraper import run_op_scraper, run_price_scraper, insert_settlement_date, insert_init_op, insert_init_price
from .services.analyzer import run_analysis, get_revenue, get_risk_condition
from .services.order import open_orders, close_orders
from .services.line import push_message_test
from .services.shioaji import get_position, get_api_usage, get_account_margin


@api_view()
@require_secret_token
def view_dtl(request):
    return Response({'success': 200, 'message': 'api'})


@api_view(['POST'])
@require_secret_token
def test(request):
    get_risk_condition()
    return Response('')


@api_view(['POST'])
@require_secret_token
def usage(request):
    data = get_api_usage()
    return Response(data)


@api_view(['POST'])
@require_secret_token
def position(request):
    data = get_position()
    return Response(data)


@api_view(['GET'])
@require_secret_token
def revenue(request, timeframe=None):
    if not timeframe:
        return Response({"error": "Timeframe is required"}, status=status.HTTP_400_BAD_REQUEST)
    if timeframe not in ['week', 'month', 'year']:
        return Response({"error": "Invalid timeframe"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_revenue(timeframe)
    return Response(data)


@api_view(['POST'])
@require_secret_token
def init_op_price(request):
    insert_init_op()
    insert_init_price()
    return Response('')


@api_view(['POST', 'DELETE'])
@require_secret_token
def order(request):
    if request.method == 'POST':
        open_orders()
        print('ok')
        return Response('')
    elif request.method == 'DELETE':
        close_orders()
        print('ok')
        return Response('')


@api_view(['POST'])
@require_secret_token
def analysis(request):
    run_analysis()
    print('ok')
    return Response('')


@api_view(['POST'])
@require_secret_token
def op_scraper(request):
    run_op_scraper()
    print('ok')
    return Response('')


@api_view(['POST'])
@require_secret_token
def price_scraper(request):
    run_price_scraper()
    print('ok')
    return Response('')


@api_view(['POST'])
@require_secret_token
def settlement(request):
    if request.method == 'POST':
        insert_settlement_date()
        print('ok')
        return Response('')
