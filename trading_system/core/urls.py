from django.urls import path
from .views import (
    view_dtl,
    op_scraper,
    price_scraper,
    settlement,
    test,
    analysis,
    order,
    init_op_price,
    revenue,
    position,
    usage,
    some_order,
)

urlpatterns = [
    path("", view_dtl, name="execute_back_test_task"),
    path("test", test, name="execute_back_test_task"),
    path("op", op_scraper, name="update_op_table"),
    path("price", price_scraper, name="update_price_table"),
    path("settlement", settlement, name="insert_settlement"),
    path("analysis", analysis, name="analysis_signal"),
    path("order", order, name="order"),
    path("some-order", some_order, name="some_order"),
    path("revenue/<str:timeframe>/", revenue, name="get_revenue"),
    path("position", position, name="get_position"),
    path("usage", usage, name="get_usage"),
    path("init", init_op_price, name="init"),
]
