from typing import TypedDict, List, Union


class BubbleMessage(TypedDict, total=False):
    header: str
    body: List[Union[str, int]]
    footer: str


class EMOJIMap(TypedDict):
    success: str
    failure: str
    buy: str
    sell: str
    bull: str
    bear: str
    profit: str
    loss: str
    up_chart: str
    down_chart: str
    thinking_face: str
    eyes: str
