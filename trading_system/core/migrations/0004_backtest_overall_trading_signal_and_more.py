# Generated by Django 5.0.6 on 2024-07-14 16:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_backtest_fr_trading_signal_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="backtest",
            name="overall_trading_signal",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="signal",
            name="overall_trading_signal",
            field=models.IntegerField(default=0),
        ),
    ]
