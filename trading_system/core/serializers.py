from rest_framework import serializers
from .models import (
    OptionData,
    PriceData,
    Settlement,
    Signal,
    Order,
    Revenue,
    Backtest,
    UnfulfilledOp,
    UnfulfilledFt,
)


class BaseModelSerializer(serializers.ModelSerializer):

    class Meta:
        fields = "__all__"


class OptionDataSerializer(BaseModelSerializer):

    class Meta(BaseModelSerializer.Meta):
        model = OptionData


class PriceDataSerializer(BaseModelSerializer):

    class Meta(BaseModelSerializer.Meta):
        model = PriceData


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


class UnfulfilledOpSerializer(BaseModelSerializer):

    class Meta(BaseModelSerializer.Meta):
        model = UnfulfilledOp


class UnfulfilledFtSerializer(BaseModelSerializer):

    class Meta(BaseModelSerializer.Meta):
        model = UnfulfilledFt
