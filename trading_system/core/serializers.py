from rest_framework import serializers
from .models import OptionData, DayPrice, NightPrice, Settlement, Signal, Order, Revenue, Backtest


class BaseModelSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'


class OptionDataSerializer(BaseModelSerializer):

    class Meta(BaseModelSerializer.Meta):
        model = OptionData


class DayPriceSerializer(BaseModelSerializer):

    class Meta(BaseModelSerializer.Meta):
        model = DayPrice


class NightPriceSerializer(BaseModelSerializer):

    class Meta(BaseModelSerializer.Meta):
        model = NightPrice


class SettlementSerializer(BaseModelSerializer):

    class Meta(BaseModelSerializer.Meta):
        model = Settlement


class SignalSerializer(BaseModelSerializer):

    class Meta(BaseModelSerializer.Meta):
        model = Signal


class OrderSerializer(BaseModelSerializer):

    class Meta(BaseModelSerializer.Meta):
        model = Order


class RevenueSerializer(BaseModelSerializer):

    class Meta(BaseModelSerializer.Meta):
        model = Revenue


class BacktestSerializer(BaseModelSerializer):

    class Meta(BaseModelSerializer.Meta):
        model = Backtest
