
from sessions import session, save_session
from get_game_config import get_name_from_item_id, get_attribute_from_mission_id
from constants import Constant
from engine import apply_cost, apply_collect, apply_collect_xp

def command(USERID, data):
    timestamp = data["ts"]
    first_number = data["first_number"]
    accessToken = data["accessToken"]
    tries = data["tries"]
    publishActions = data["publishActions"]
    commands = data["commands"]
    
    for i, comm in enumerate(commands):
        cmd = comm["cmd"]
        args = comm["args"]
        do_command(USERID, cmd, args)
    save_session(USERID) # Save session

def do_command(USERID, cmd, args):
    save = session(USERID)
    print (" [+] COMMAND: ", cmd, "(", args, ") -> ", sep='', end='')

    if cmd == Constant.CMD_GAME_STATUS:
        print(" ".join(args))

    elif cmd == Constant.CMD_BUY:
        id = args[0]
        x = args[1]
        y = args[2]
        frame = args[3] # TODO ??
        town_id = args[4]
        bool_dont_modify_resources = bool(args[5]) # 1 if the game "buys" for you, so does not substract whatever the item cost is.
        price_multiplier = args[6]
        type = args[7]
        print("Add", str(get_name_from_item_id(id)), "at", f"({x},{y})")
        collected_at_timestamp = 0 # TODO 
        level = 0 # TODO 
        orientation = 0
        map = save["maps"][town_id]
        if not bool_dont_modify_resources:
            apply_cost(save["playerInfo"], map, id, price_multiplier)
        map["items"] += [[id, x, y, orientation, collected_at_timestamp, level]]
    
    elif cmd == Constant.CMD_COMPLETE_TUTORIAL:
        tutorial_step = args[0]
        print("Tutorial step", tutorial_step, "reached.")
        if tutorial_step >= 31: # 31 is Dragon choosing. After that, you have some freedom. There's at least until step 45.
            print("Tutorial COMPLETED!")
            save["playerInfo"]["completed_tutorial"] = 1
    
    elif cmd == Constant.CMD_MOVE:
        ix = args[0]
        iy = args[1]
        id = args[2]
        newx = args[3]
        newy = args[4]
        frame = args[5]
        town_id = args[6]
        reason = args[7] # "Unitat", "moveTo", "colisio", "MouseUsed"
        print("Move", str(get_name_from_item_id(id)), "from", f"({ix},{iy})", "to", f"({newx},{newy})")
        map = save["maps"][town_id]
        for item in map["items"]:
            if item[0] == id and item[1] == ix and item[2] == iy:
                item[1] = newx
                item[2] = newy
                break
    
    elif cmd == Constant.CMD_COLLECT:
        x = args[0]
        y = args[1]
        town_id = args[2]
        id = args[3]
        num_units_contained_when_harvested = args[4]
        resource_multiplier = args[5]
        cash_to_substract = args[6]
        print("Collect", str(get_name_from_item_id(id)))
        map = save["maps"][town_id]
        apply_collect(save["playerInfo"], map, id, resource_multiplier)
        save["playerInfo"]["cash"] = min(save["playerInfo"]["cash"] - cash_to_substract, 0)
    
    elif cmd == Constant.CMD_SELL:
        x = args[0]
        y = args[1]
        id = args[2]
        town_id = args[3]
        bool_dont_modify_resources = args[4]
        reason = args[5]
        print("Remove", str(get_name_from_item_id(id)), "from", f"({x},{y}). Reason: {reason}")
        map = save["maps"][town_id]
        for item in map["items"]:
            if item[0] == id and item[1] == x and item[2] == y:
                map["items"].remove(item)
                break
        if not bool_dont_modify_resources:
            pass
    
    elif cmd == Constant.CMD_KILL:
        x = args[0]
        y = args[1]
        id = args[2]
        town_id = args[3]
        type = args[4]
        print("Kill", str(get_name_from_item_id(id)), "from", f"({x},{y}).")
        map = save["maps"][town_id]
        for item in map["items"]:
            if item[0] == id and item[1] == x and item[2] == y:
                apply_collect_xp(map, id)
                map["items"].remove(item)
                break
    
    elif cmd == Constant.CMD_COMPLETE_MISSION:
        mission_id = args[0]
        skipped_with_cash = bool(args[1])
        if skipped_with_cash:
            cash_to_substract = 0 # TODO 
            save["playerInfo"]["cash"] = min(save["playerInfo"]["cash"] - cash_to_substract, 0)
        save["privateState"]["completedMissions"] += [mission_id]
        print("Complete mission", mission_id + ":", str(get_attribute_from_mission_id(mission_id, "title")))
    
    elif cmd == Constant.CMD_REWARD_MISSION:
        town_id = args[0]
        mission_id = args[1]
        reward = int(get_attribute_from_mission_id(mission_id, "reward")) # xp
        save["maps"][town_id]["xp"] += reward
        save["privateState"]["rewardedMissions"] += [mission_id]
        print("Reward mission", mission_id + ":", str(get_attribute_from_mission_id(mission_id, "title")))
    
    else:
        print(f"Unhandled command '{cmd}' -> args", args)
        return
    