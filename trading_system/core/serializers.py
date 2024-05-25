from rest_framework import serializers
from .models import OptionData, DayPrice, NightPrice, Settlement, Signal, Order, Revenue, Backtest


class OptionDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = OptionData
        fields = '__all__'


class DayPriceSerializer(serializers.ModelSerializer):

    class Meta:
        model = DayPrice
        fields = '__all__'


class NightPriceSerializer(serializers.ModelSerializer):

    class Meta:
        model = NightPrice
        fields = '__all__'


class SettlementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Settlement
        fields = '__all__'


class SignalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Signal
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = '__all__'


class RevenueSerializer(serializers.ModelSerializer):

    class Meta:
        model = Revenue
        fields = '__all__'


class BacktestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Backtest
        fields = '__all__'
