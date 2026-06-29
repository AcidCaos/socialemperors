import time

from get_game_config import get_attribute_from_item_id

def apply_cost(playerInfo: dict, map: dict, id: int, price_multiplier: int) -> None:
    cost_val = get_attribute_from_item_id(id, "cost")
    if cost_val is None:
        return
    cost = int(float(price_multiplier) * int(cost_val))
    cost_type = get_attribute_from_item_id(id, "cost_type")
    if cost_type == "w":
        map["wood"] = max(map["wood"] - cost, 0)
    elif cost_type == "g":
        map["coins"] = max(map["coins"] - cost, 0)
    elif cost_type == "c":
        playerInfo["cash"] = max(playerInfo["cash"] - cost, 0)
    elif cost_type == "s":
        map["stone"] = max(map["stone"] - cost, 0)
    elif cost_type == "f":
        map["food"] = max(map["food"] - cost, 0)

def apply_collect(playerInfo: dict, map: dict, id: int, resource_multiplier) -> None:
    collect_val = get_attribute_from_item_id(id, "collect")
    collect = int(float(resource_multiplier) * int(collect_val)) if collect_val is not None else 0
    collect_type = get_attribute_from_item_id(id, "collect_type")
    apply_collect_xp(map, id)
    if collect_type == "w":
        map["wood"] = map["wood"] + collect
    elif collect_type == "g":
        map["coins"] = map["coins"] + collect
    elif collect_type == "c":
        playerInfo["cash"] = playerInfo["cash"] + collect
    elif collect_type == "s":
        map["stone"] = map["stone"] + collect
    elif collect_type == "f":
        map["food"] = map["food"] + collect

def apply_collect_xp(map: dict, id: int) -> None:
    collect_xp_val = get_attribute_from_item_id(id, "collect_xp")
    collect_xp = int(collect_xp_val) if collect_xp_val is not None else 0
    map["xp"] = map["xp"] + collect_xp

def timestamp_now() -> int:
    return int(time.time())