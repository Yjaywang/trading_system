from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
import core.models as models
import core.serializers as serializers
from rest_framework import status
import json
from .services.line import analysis_result


@api_view()
def view_dtl(request):
    return Response({'success': 200, 'message': 'api'})


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def option_data_list(request):
    if request.method == 'GET':
        option_data = models.OptionData.objects.all()
        option_data = models.OptionData.objects.filter(date="2023-05-24")
        serializer = serializers.OptionDataSerializer(option_data, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        return Response(analysis_result('test'))

        # serializer = serializers.OptionDataSerializer(data=request.data)
        # if serializer.is_valid():
        #     serializer.save()
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
