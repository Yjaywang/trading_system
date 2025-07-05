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
DAILY_CRON_STATUS = 'daily_cron_status'

EMOJI_MAP: EMOJIMap = {
    'success': "\u2705",           # ✅
    'failure': "\u274C",           # ❌
    "buy": "\U0001F7E2",           # 🟢 Green circle'
    "sell": "\U0001F534",          # 🔴 Red circle
    "bull": "\U0001F680",          # 🚀 Rocket
    "bear": "\U0001F4A3",          # 💣 Bomb
    "profit": "\U0001F389",        # 🎉 Party popper
    "loss": "\U0001F4B8",          # 💸 Money with wings
    "up_chart": "\U0001F4C8",      # 📈 Chart increasing
    "down_chart": "\U0001F4C9",    # 📉 Chart decreasing
    "thinking_face": "\U0001F914", # 🤔
    "eyes": "\U0001F440"            # 👀
}

TRADING_SIGNAL_MAP = {
    1: EMOJI_MAP['bull'],  # Buy signal
    -1: EMOJI_MAP['bear'], # Sell signal
    0: EMOJI_MAP['eyes'],  # Neutral signal
}

LINE_BUBBLE_MESSAGE_TEMPLATE = {
    "type": "bubble",
    "header": {
        "type":
            "box",
        "layout":
            "vertical",
        "contents": [{
            "type": "text", "text": "default header message", "weight": "bold", "style": "italic", "align": "center"
        }]
    },
    "body": {
        "type": "box", "layout": "vertical", "contents": [{
            "type": "text", "text": "default body message"
        }]
    },
    "footer": {
        "type": "box",
        "layout": "vertical",
        "contents": [{
            "type": "text", "align": "center", "text": "default footer message", "weight": "bold"
        }]
    }
}
