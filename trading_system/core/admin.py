from django.contrib import admin
from .models import OptionData, DayPrice, NightPrice, Settlement, Signal, Order, Revenue, Backtest
# Register your models here.

admin.site.register(OptionData)
admin.site.register(DayPrice)
admin.site.register(NightPrice)
admin.site.register(Settlement)
admin.site.register(Signal)
admin.site.register(Order)
admin.site.register(Revenue)
admin.site.register(Backtest)
