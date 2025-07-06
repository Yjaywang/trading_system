from ..types import EMOJIMap

DATE_FORMAT = "%Y/%m/%d"
DATE_FORMAT_2 = "%Y-%m-%d"
WEEKDAY_TRANSFORM = {
    0: "Mon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun",
}
SLEEP_DURATION = 3

POINT_VALUE = {"TXF": 200, "MXF": 50}
DAILY_CRON_STATUS = "daily_cron_status"

EMOJI_MAP: EMOJIMap = {
    "success": "\u2705",  # ✅
    "failure": "\u274c",  # ❌
    "buy": "\U0001f7e2",  # 🟢 Green circle'
    "sell": "\U0001f534",  # 🔴 Red circle
    "bull": "\U0001f680",  # 🚀 Rocket
    "bear": "\U0001f4a3",  # 💣 Bomb
    "profit": "\U0001f389",  # 🎉 Party popper
    "loss": "\U0001f4b8",  # 💸 Money with wings
    "up_chart": "\U0001f4c8",  # 📈 Chart increasing
    "down_chart": "\U0001f4c9",  # 📉 Chart decreasing
    "thinking_face": "\U0001f914",  # 🤔
    "eyes": "\U0001f440",  # 👀
}

TRADING_SIGNAL_MAP = {
    1: EMOJI_MAP["bull"],  # Buy signal
    -1: EMOJI_MAP["bear"],  # Sell signal
    0: EMOJI_MAP["eyes"],  # Neutral signal
}

LINE_BUBBLE_MESSAGE_TEMPLATE = {
    "type": "bubble",
    "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": "default header message",
                "weight": "bold",
                "style": "italic",
                "align": "center",
            }
        ],
    },
    "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [{"type": "text", "text": "default body message"}],
    },
    "footer": {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "align": "center",
                "text": "default footer message",
                "weight": "bold",
            }
        ],
    },
}
