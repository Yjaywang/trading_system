from django.db import models

# Create your models here.


#null=True for data layer，blank=True for validation layer。
class OptionData(models.Model):
    option_id = models.AutoField(primary_key=True)
    year = models.IntegerField()
    month = models.IntegerField()
    date = models.CharField(max_length=10)  # YYYY-MM-DD
    day = models.CharField(max_length=10)  # Mon, Tue, Wed, Thu, Fri
    tw_trade_call_count = models.IntegerField()
    tw_trade_call_amount = models.IntegerField()
    fr_trade_call_count = models.IntegerField()
    fr_trade_call_amount = models.IntegerField()
    tw_trade_put_count = models.IntegerField()
    tw_trade_put_amount = models.IntegerField()
    fr_trade_put_count = models.IntegerField()
    fr_trade_put_amount = models.IntegerField()
    call_count = models.IntegerField()
    call_amount = models.IntegerField()
    put_count = models.IntegerField()
    put_amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)  # created time
    updated_at = models.DateTimeField(auto_now=True)  # updated time

    def __str__(self):
        return f'{self.date} - {self.day} - {self.option_id}'


class DayPrice(models.Model):
    day_price_id = models.AutoField(primary_key=True)
    year = models.IntegerField()
    month = models.IntegerField()
    date = models.CharField(max_length=10)  # YYYY-MM-DD
    day = models.CharField(max_length=10)  # Mon, Tue, Wed, Thu, Fri
    open = models.IntegerField()
    high = models.IntegerField()
    low = models.IntegerField()
    close = models.IntegerField()
    volume = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)  # created time
    updated_at = models.DateTimeField(auto_now=True)  # updated time

    def __str__(self):
        return f'{self.date} - {self.day} - {self.day_price_id}'


class NightPrice(models.Model):
    night_price_id = models.AutoField(primary_key=True)
    year = models.IntegerField()
    month = models.IntegerField()
    date = models.CharField(max_length=10)  # YYYY-MM-DD
    day = models.CharField(max_length=10)  # Mon, Tue, Wed, Thu, Fri
    open = models.IntegerField()
    high = models.IntegerField()
    low = models.IntegerField()
    close = models.IntegerField()
    volume = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)  # created time
    updated_at = models.DateTimeField(auto_now=True)  # updated time

    def __str__(self):
        return f'{self.date} - {self.day} - {self.night_price_id}'


class Settlement(models.Model):
    settlement_id = models.AutoField(primary_key=True)
    year = models.IntegerField()
    month = models.IntegerField()
    date = models.CharField(max_length=10)  # YYYY-MM-DD
    day = models.CharField(max_length=10)  # Mon, Tue, Wed, Thu, Fri
    created_at = models.DateTimeField(auto_now_add=True)  # created time
    updated_at = models.DateTimeField(auto_now=True)  # updated time

    def __str__(self):
        return f'{self.date} - {self.day} - {self.settlement_id}'


class Signal(models.Model):
    option_data = models.ForeignKey(OptionData,
                                    on_delete=models.CASCADE,
                                    related_name='Signals')
    signal_id = models.AutoField(primary_key=True)
    year = models.IntegerField()
    month = models.IntegerField()
    date = models.CharField(max_length=10)  # YYYY-MM-DD
    day = models.CharField(max_length=10)  # Mon, Tue, Wed, Thu, Fri
    settlement_signal = models.IntegerField(
        default=0)  # default 0, settlement day is 1
    reverse_signal = models.IntegerField(
        default=0)  # default 0, 1st day after settlement is 1
    trading_signal = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)  # created time
    updated_at = models.DateTimeField(auto_now=True)  # updated time

    def __str__(self):
        return f'{self.date} - {self.day} - {self.signal_id}'


class Order(models.Model):
    signal_data = models.ForeignKey(Signal,
                                    on_delete=models.CASCADE,
                                    related_name='Orders')
    order_id = models.AutoField(primary_key=True)
    year = models.IntegerField()
    month = models.IntegerField()
    date = models.CharField(max_length=10)  # YYYY-MM-DD
    day = models.CharField(max_length=10)  # Mon, Tue, Wed, Thu, Fri
    prodcut = models.CharField(max_length=20)
    quantity = models.IntegerField()
    action = models.CharField(max_length=20)  # buy, sell, no action
    deal_price = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)  # created time
    updated_at = models.DateTimeField(auto_now=True)  # updated time

    def __str__(self):
        return f'{self.date} - {self.day} - {self.order_id}'


class Revenue(models.Model):
    signal_data = models.ForeignKey(Signal,
                                    on_delete=models.CASCADE,
                                    related_name='Revenues')
    order_data = models.ForeignKey(Order,
                                   on_delete=models.CASCADE,
                                   related_name='Revenues')
    revenue_id = models.AutoField(primary_key=True)
    year = models.IntegerField()
    month = models.IntegerField()
    date = models.CharField(max_length=10)  # YYYY-MM-DD
    day = models.CharField(max_length=10)  # Mon, Tue, Wed, Thu, Fri
    prodcut = models.CharField(max_length=20)
    quantity = models.IntegerField()
    action = models.CharField(max_length=20)  # buy, sell, no action
    open_price = models.IntegerField()
    close_price = models.IntegerField()
    revenue = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)  # created time
    updated_at = models.DateTimeField(auto_now=True)  # updated time

    def __str__(self):
        return f'{self.date} - {self.day} - {self.revenue_id}'


class Backtest(models.Model):
    option_data = models.ForeignKey(OptionData,
                                    on_delete=models.CASCADE,
                                    related_name='Backtests')
    signal_data = models.ForeignKey(Signal,
                                    on_delete=models.CASCADE,
                                    related_name='Backtests')
    backtest_id = models.AutoField(primary_key=True)
    year = models.IntegerField()
    month = models.IntegerField()
    date = models.CharField(max_length=10)  # YYYY-MM-DD
    day = models.CharField(max_length=10)  # Mon, Tue, Wed, Thu, Fri
    open = models.IntegerField()
    high = models.IntegerField()
    low = models.IntegerField()
    close = models.IntegerField()
    diff_high = models.IntegerField()
    diff_low = models.IntegerField()
    diff_close = models.IntegerField()
    tw_trade_call_count = models.IntegerField()
    tw_trade_call_amount = models.IntegerField()
    fr_trade_call_count = models.IntegerField()
    fr_trade_call_amount = models.IntegerField()
    tw_trade_put_count = models.IntegerField()
    tw_trade_put_amount = models.IntegerField()
    fr_trade_put_count = models.IntegerField()
    fr_trade_put_amount = models.IntegerField()
    call_count = models.IntegerField()
    call_amount = models.IntegerField()
    put_count = models.IntegerField()
    put_amount = models.IntegerField()
    settlement_signal = models.IntegerField()
    reverse_signal = models.IntegerField(
        default=0)  # default 0, 1st day after settlement is 1
    trading_signal = models.IntegerField()
    result = models.IntegerField()
    money_status = models.CharField(max_length=10)  # loss, gain, even
    max_loss = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)  # created time
    updated_at = models.DateTimeField(auto_now=True)  # updated time

    def __str__(self):
        return f'{self.date} - {self.day} - {self.backtest_id}'
