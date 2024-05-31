from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .services.scraper import run_op_scraper, run_price_scraper, insert_settlement_date, insert_init_op, insert_init_price
from .services.analyzer import run_analysis
from .services.order import open_orders, close_orders


@api_view()
def view_dtl(request):
    return Response({'success': 200, 'message': 'api'})


@api_view(['POST'])
def test(request):
    return Response('')


@api_view(['POST'])
def init_op_price(request):
    insert_init_op()
    insert_init_price()
    return Response('')


@api_view(['POST', 'DELETE'])
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
def analysis(request):
    run_analysis()
    print('ok')
    return Response('')


@api_view(['POST'])
def op_scraper(request):
    run_op_scraper()
    print('ok')
    return Response('')


@api_view(['POST'])
def price_scraper(request):
    run_price_scraper()
    print('ok')
    return Response('')


@api_view(['POST'])
def settlement(request):
    if request.method == 'POST':
        insert_settlement_date()
        print('ok')
        return Response('')
