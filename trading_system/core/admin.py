from django.contrib import admin
from .models import OptionData, PriceData, Settlement, Signal, Order, Revenue, Backtest

# Register your models here.

admin.site.register(OptionData)
admin.site.register(PriceData)
admin.site.register(Settlement)
admin.site.register(Signal)
admin.site.register(Order)
admin.site.register(Revenue)
admin.site.register(Backtest)
