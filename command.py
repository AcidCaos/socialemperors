
from sessions import session, save_session
from get_game_config import get_game_config, get_name_from_item_id, get_attribute_from_mission_id, get_xp_from_level, get_attribute_from_item_id
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
            xp = int(get_attribute_from_item_id(id, "xp"))
            map["xp"] = map["xp"] + xp
        map["items"] += [[id, x, y, orientation, collected_at_timestamp, level]]
    
    elif cmd == Constant.CMD_COMPLETE_TUTORIAL:
        tutorial_step = args[0]
        print("Tutorial step", tutorial_step, "reached.")
        if tutorial_step >= 31: # 31 is Dragon choosing. After that, you have some freedom. There's at least until step 45.
            print("Tutorial COMPLETED!")
            save["playerInfo"]["completed_tutorial"] = 1
            save["privateState"]["dragonNestActive"] = 1 
    
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
        num_units_contained_when_harvested = args[4]#TODO does this affect multiplier?
        resource_multiplier = args[5]
        cash_to_substract = args[6]
        print("Collect", str(get_name_from_item_id(id)))
        map = save["maps"][town_id]
        apply_collect(save["playerInfo"], map, id, resource_multiplier)
        save["playerInfo"]["cash"] = max(save["playerInfo"]["cash"] - cash_to_substract, 0)
    
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
            price_multiplier = -0.05
            if get_attribute_from_item_id(id, "cost_type") != "c":
                apply_cost(save["playerInfo"], save["maps"][town_id], id, price_multiplier)
    
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
            save["playerInfo"]["cash"] = max(save["playerInfo"]["cash"] - cash_to_substract, 0)
        save["privateState"]["completedMissions"] += [mission_id]
        print("Complete mission", mission_id, ":", str(get_attribute_from_mission_id(mission_id, "title")))
    
    elif cmd == Constant.CMD_REWARD_MISSION:
        town_id = args[0]
        mission_id = args[1]
        reward = int(get_attribute_from_mission_id(mission_id, "reward")) # gold
        save["maps"][town_id]["coins"] += reward   
        save["privateState"]["rewardedMissions"] += [mission_id]
        print("Reward mission", mission_id, ":", str(get_attribute_from_mission_id(mission_id, "title")))
    
    elif cmd == Constant.CMD_PUSH_UNIT:
        unit_x = args[0]
        unit_y = args[1]
        unit_id = args[2]
        b_x = args[3]
        b_y = args[4]
        town_id = args[5]
        print("Push", str(get_name_from_item_id(unit_id)), "to", f"({b_x},{b_y}).")
        map = save["maps"][town_id]
        # Unit into building
        for item in map["items"]:
            if item[1] == b_x and item[2] == b_y:
                if len(item) < 7:
                    item += [[]]
                item[6] += [unit_id]
                break
        # Remove unit
        for item in map["items"]:
            if item[0] == unit_id and item[1] == unit_x and item[2] == unit_y:
                map["items"].remove(item)
                break
    
    elif cmd == Constant.CMD_POP_UNIT:
        b_x = args[0]
        b_y = args[1]
        town_id = args[2]
        unit_id = args[3]
        unit_x = args[4]
        unit_y = args[5]
        unit_frame = args[2]
        print("Pop", str(get_name_from_item_id(unit_id)), "from", f"({b_x},{b_y}).")
        map = save["maps"][town_id]
        # Remove unit from building
        for item in map["items"]:
            if item[1] == b_x and item[2] == b_y:
                if len(item) < 7:
                    break
                item[6].remove(unit_id)
                break
        # Spawn unit outside
        collected_at_timestamp = 0 # TODO 
        level = 0 # TODO 
        orientation = 0
        map["items"] += [[unit_id, unit_x, unit_y, orientation, collected_at_timestamp, level]]
    
    elif cmd == Constant.CMD_RT_LEVEL_UP:
        new_level = args[0]
        print("Level Up!:", new_level)
        map = save["maps"][0] # TODO : xp must be general, since theres no given town_id
        map["level"] = args[0]
        current_xp = map["xp"]
        min_expected_xp = get_xp_from_level(max(0, new_level - 1))
        map["xp"] = max(min_expected_xp, current_xp) # try to fix problems with not counting XP... by keeping up with client-side level counting

    elif cmd == Constant.CMD_EXPAND:
        land_id = args[0]
        resource = args[1]
        town_id = int(args[2])
        print("Expansion", land_id, "purchased")
        map = save["maps"][town_id]
        if land_id in map["expansions"]:
            return
        # Substract resources
        expansion_prices = get_game_config()["expansion_prices"]
        exp = expansion_prices[len(map["expansions"])]
        if resource == "gold":
            to_substract = exp["coins"]
            save["maps"][town_id]["coins"] = max(save["maps"][town_id]["coins"] - to_substract, 0)
        elif resource == "cash":
            to_substract = exp["cash"]
            save["playerInfo"]["cash"] = max(save["playerInfo"]["cash"] - to_substract, 0)
        # Add expansion
        map["expansions"].append(land_id)
        print(f"map expansion '{land_id}' added.")

    elif cmd == Constant.CMD_NAME_MAP:
        town_id =int(args[0])
        new_name = args[1]
        save["playerInfo"]["map_names"][town_id] = new_name
        print(f"map name changed to '{new_name}'.")

    elif cmd == Constant.CMD_EXCHANGE_CASH:
        town_id = args[0]
        save["playerInfo"]["cash"] = max(save["playerInfo"]["cash"] - 5, 0)#maybe make function for editing resources
        save["maps"][town_id]["coins"] += 2500
        print("Exchange successful.")

    elif cmd == Constant.CMD_STORE_ITEM:
        x = args[0]
        y = args[1]
        town_id = int(args[2])
        item_id = args[3]
        map = save["maps"][town_id]
        for item in map["items"]:
            if item[0] == item_id and item[1] == x and item[2] == y:
                map["items"].remove(item)
                break
        length = len(save["privateState"]["gifts"])
        if length <= item_id:
            for i in range(item_id - length + 1):
                save["privateState"]["gifts"].append(0)
        save["privateState"]["gifts"][item_id] += 1
        print("Stored",str(get_name_from_item_id(item_id)), "from", f"({x},{y})")

    elif cmd == Constant.CMD_PLACE_GIFT:
        item_id = args[0]
        x = args[1]
        y = args[2]
        town_id = args[3]#unsure, both 3 and 4 seem to stay 0
        args[4]#unknown yet
        items = save["maps"][town_id]["items"]
        orientation = 0#TODO
        collected_at_timestamp = 0#TODO
        level = 0
        items += [[item_id, x, y, orientation, collected_at_timestamp, level]]#maybe make function for adding items
        print("Add", str(get_name_from_item_id(item_id)), "at", f"({x},{y})")
        save["privateState"]["gifts"][item_id] -= 1
        if save["privateState"]["gifts"][item_id] == 0: #removes excess zeros at end if necessary
            while(save["privateState"]["gifts"][-1] == 0):
                save["privateState"]["gifts"].pop()  

    elif cmd == Constant.CMD_SELL_GIFT:
        item_id = args[0]
        town_id = args[1]
        gifts = save["privateState"]["gifts"]
        gifts[item_id] -= 1
        if gifts[item_id] == 0: #removes excess zeros at end if necessary
            while(len(gifts) != 0 and gifts[-1] == 0):
                gifts.pop()
        price_multiplier = -0.05
        if get_attribute_from_item_id(item_id, "cost_type") != "c":
            apply_cost(save["playerInfo"], save["maps"][town_id], item_id, price_multiplier)
        print("gift", str(get_name_from_item_id(item_id)), "sold on town:",town_id)
    
    elif cmd == Constant.CMD_ACTIVATE_DRAGON:
        currency = args[0]
        if currency == 'c':
            save["playerInfo"]["cash"] = max(int(save["playerInfo"]["cash"] - 50), 0)
        elif currency == 'g':
            map = save["maps"]
            map[0]["coins"] = max(int(map[0]["coins"] - 100000), 0)
        save["privateState"]["dragonNestActive"] = 1
        print("Dragon nest activated.")
    
    elif cmd == Constant.CMD_DESACTIVATE_DRAGON:
        pState = save["privateState"]
        pState["dragonNestActive"] = 0# reset step and dragon numbers
        pState["stepNumber"] = 0
        pState["dragonNumber"] = 0
        print("Dragon nest deactivated.")

    elif cmd == Constant.CMD_NEXT_DRAGON_STEP:
        pState = save["privateState"]
        pState["stepNumber"] += 1
        print("DragonStep increased.")

    elif cmd == Constant.CMD_NEXT_DRAGON:
        pState = save["privateState"]
        pState["stepNumber"] = 0
        pState["dragonNumber"] += 1
        print("DragonStep reset and dragonNumber increased.")

    elif cmd == Constant.CMD_DRAGON_BUY_STEP_CASH:
        price = args[0]
        save["playerInfo"]["cash"] = max(int(save["playerInfo"]["cash"] - price), 0)
        #TODO remove the timer

    elif cmd == Constant.CMD_RIDER_BUY_STEP_CASH:
        price = args[0]
        save["playerInfo"]["cash"] = max(int(save["playerInfo"]["cash"] - price), 0)
        #TODO remove the timer

    elif cmd == Constant.CMD_NEXT_RIDER_STEP:
        pState = save["privateState"]
        pState["riderStepNumber"] += 1
        print("riderStep increased.")
    
    elif cmd == Constant.CMD_SELECT_RIDER:
        number = int(args[0])
        pState = save["privateState"]
        if number == 1 or number == 2 or number == 3:
            pState["riderNumber"] = number
            print("Rider",number,"Selected.")
        else:
            pState["riderNumber"] = 0
            pState["riderStepNumber"] = 0
            print("Rider reset.")
    
    elif cmd == Constant.CMD_ORIENT:
        x = args[0]
        y = args[1]
        new_orientation = args[2]
        town_id = args[3]
        map = save["maps"][town_id]
        for item in map["items"]:
            if item[1] == x and item[2] == y:
                item[3] = new_orientation
                print("item at",f"({x},{y})","changed to orientation",new_orientation)
                break
    
    elif cmd == Constant.CMD_MONSTER_BUY_STEP_CASH:
        price = args[0]
        save["playerInfo"]["cash"] = max(int(save["playerInfo"]["cash"] - price), 0)
        #TODO remove the timer
    
    elif cmd == Constant.CMD_ACTIVATE_MONSTER:
        currency = args[0]
        if currency == 'c':
            save["playerInfo"]["cash"] = max(int(save["playerInfo"]["cash"] - 50), 0)
        elif currency == 'g':
            map = save["maps"]
            map[0]["coins"] = max(int(map[0]["coins"] - 100000), 0)
        save["privateState"]["monsterNestActive"] = 1
        print("Monster nest activated.")
    
    elif cmd == Constant.CMD_ACTIVATE_MONSTER:
        currency = args[0]
        if currency == 'c':
            save["playerInfo"]["cash"] = max(int(save["playerInfo"]["cash"] - 50), 0)
        elif currency == 'g':
            map = save["maps"]
            map[0]["coins"] = max(int(map[0]["coins"] - 100000), 0)
        save["privateState"]["monsterNestActive"] = 1
        print("Monster nest activated.")
    
    elif cmd == Constant.CMD_DESACTIVATE_MONSTER:#cmd called too late
        pState = save["privateState"]
        pState["monsterNestActive"] = 0
        pState["stepMonsterNumber"] = 0
        pState["MonsterNumber"] = 0
        print("Monster nest deactivated.")

    elif cmd == Constant.CMD_NEXT_MONSTER_STEP:
        pState = save["privateState"]
        pState["stepMonsterNumber"] += 1
        print("Monster Step increased.")

    elif cmd == Constant.CMD_NEXT_MONSTER:
        pState = save["privateState"]
        pState["stepMonsterNumber"] = 0
        pState["monsterNumber"] += 1
        print("MonsterStep reset and MonsterNumber increased.")

    else:
        print(f"Unhandled command '{cmd}' -> args", args)
        return
    
