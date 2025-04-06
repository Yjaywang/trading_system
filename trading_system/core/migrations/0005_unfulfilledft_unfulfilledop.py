# Generated by Django 5.0.6 on 2025-04-06 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_backtest_overall_trading_signal_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="UnfulfilledFt",
            fields=[
                (
                    "unfulfilled_ft_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("year", models.IntegerField()),
                ("month", models.IntegerField()),
                ("date", models.DateField()),
                (
                    "day",
                    models.CharField(
                        choices=[
                            ("Mon", "Mon"),
                            ("Tue", "Tue"),
                            ("Wed", "Wed"),
                            ("Thu", "Thu"),
                            ("Fri", "Fri"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "trader",
                    models.CharField(
                        choices=[("dt", "tw"), ("it", "it"), ("fi", "fr")],
                        max_length=10,
                    ),
                ),
                (
                    "future_name",
                    models.CharField(
                        choices=[
                            ("TX", "臺股期貨"),
                            ("TE", "電子期貨"),
                            ("TF", "金融期貨"),
                            ("MTX", "小型臺指期貨"),
                            ("SF", "股票期貨"),
                            ("ETF", "ETF期貨"),
                            ("subtotal", "期貨小計"),
                        ],
                        max_length=10,
                    ),
                ),
                ("unfulfilled_count", models.IntegerField()),
                ("unfulfilled_amount", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="UnfulfilledOp",
            fields=[
                (
                    "unfulfilled_op_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("year", models.IntegerField()),
                ("month", models.IntegerField()),
                ("date", models.DateField()),
                (
                    "day",
                    models.CharField(
                        choices=[
                            ("Mon", "Mon"),
                            ("Tue", "Tue"),
                            ("Wed", "Wed"),
                            ("Thu", "Thu"),
                            ("Fri", "Fri"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "op_type",
                    models.CharField(
                        choices=[("call", "call"), ("put", "put")], max_length=10
                    ),
                ),
                (
                    "direction",
                    models.CharField(
                        choices=[("buy", "buy"), ("sell", "sell")], max_length=10
                    ),
                ),
                (
                    "trader",
                    models.CharField(
                        choices=[("dt", "tw"), ("fi", "fr")], max_length=10
                    ),
                ),
                ("unfulfilled_count", models.IntegerField()),
                ("unfulfilled_amount", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
