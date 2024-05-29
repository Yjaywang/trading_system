from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
import core.models as models
import core.serializers as serializers
from rest_framework import status
import json
from .services.line import push_message
from .services.scraper import run_op_scraper, run_price_scraper, insert_settlement_date, insert_op
from .services.analyzer import run_analysis
from .services.order import place_orders


@api_view()
def view_dtl(request):
    return Response({'success': 200, 'message': 'api'})


@api_view(['POST'])
def test(request):
    insert_op()
    return Response('')


@api_view(['POST'])
def order(request):
    place_orders()
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


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def option_data_list(request):
    if request.method == 'GET':
        option_data = models.OptionData.objects.all()
        # option_data = models.OptionData.objects.filter(date="2023-05-24")
        serializer = serializers.OptionDataSerializer(option_data, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # return Response(run_op_scraper())

        serializer = serializers.OptionDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        #     return Response({
        #         'msg': 'OptionData created successfully', 'data': serializer.data
        #     },
        #                     status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        serializer = serializers.OptionDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'msg': 'OptionData created successfully', 'data': serializer.data
            },
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
