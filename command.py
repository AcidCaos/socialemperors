import json
import time
from sessions import session, save_session
from get_game_config import get_game_config, get_level_from_xp, get_name_from_item_id, get_attribute_from_mission_id, get_xp_from_level, get_attribute_from_item_id, get_item_from_subcat_functional
from constants import Constant
from engine import apply_cost, apply_collect, apply_collect_xp, timestamp_now


def get_strategy_type(id):
  if id == 8:
    return "Defensive"
  if id == 9:
    return "Mid Defensive"
  if id == 7:
    return "Mid Aggressive"
  if id == 10:
    return "Aggressive"
  return "Unknown Strategy"


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
  save_session(USERID)  # Save session


def do_command(USERID, cmd, args):
  save = session(USERID)
  print(" [+] COMMAND: ", cmd, "(", args, ") -> ", sep='', end='')

  if cmd == Constant.CMD_GAME_STATUS:
    print(" ".join(args))

  elif cmd == Constant.CMD_BUY:
    id = args[0]
    x = args[1]
    y = args[2]
    frame = args[3]  # TODO ??
    town_id = args[4]
    bool_dont_modify_resources = bool(
      args[5]
    )  # 1 if the game "buys" for you, so does not substract whatever the item cost is.
    price_multiplier = args[6]
    type = args[7]
    print("Add", str(get_name_from_item_id(id)), "at", f"({x},{y})")
    collected_at_timestamp = timestamp_now()
    level = 0  # TODO
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
    if tutorial_step >= 31:  # 31 is Dragon choosing. After that, you have some freedom. There's at least until step 45.
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
    reason = args[7]  # "Unitat", "moveTo", "colisio", "MouseUsed"
    print("Move", str(get_name_from_item_id(id)), "from", f"({ix},{iy})", "to",
          f"({newx},{newy})")
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
    num_units_contained_when_harvested = args[
      4]  #TODO does this affect multiplier?
    resource_multiplier = args[5]
    cash_to_substract = args[6]
    print("Collect", str(get_name_from_item_id(id)))
    map = save["maps"][town_id]
    apply_collect(save["playerInfo"], map, id, resource_multiplier)
    save["playerInfo"]["cash"] = max(
      save["playerInfo"]["cash"] - cash_to_substract, 0)

  elif cmd == Constant.CMD_SELL:
    x = args[0]
    y = args[1]
    id = args[2]
    town_id = args[3]
    bool_dont_modify_resources = args[4]
    reason = args[5]
    print("Remove", str(get_name_from_item_id(id)), "from",
          f"({x},{y}). Reason: {reason}")
    map = save["maps"][town_id]
    for item in map["items"]:
      if item[0] == id and item[1] == x and item[2] == y:
        map["items"].remove(item)
        break
    if not bool_dont_modify_resources:
      price_multiplier = -0.05
      if get_attribute_from_item_id(id, "cost_type") != "c":
        apply_cost(save["playerInfo"], save["maps"][town_id], id,
                   price_multiplier)
    if reason == 'KILL':
      pass  # TODO : add to graveyard

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
    print("Complete mission", mission_id, ":",
          str(get_attribute_from_mission_id(mission_id, "title")))
    if skipped_with_cash:
      cash_to_substract = 0  # TODO
      save["playerInfo"]["cash"] = max(
        save["playerInfo"]["cash"] - cash_to_substract, 0)
    save["privateState"]["completedMissions"] += [mission_id]

  elif cmd == Constant.CMD_REWARD_MISSION:
    town_id = args[0]
    mission_id = args[1]
    print("Reward mission", mission_id, ":",
          str(get_attribute_from_mission_id(mission_id, "title")))
    reward = int(get_attribute_from_mission_id(mission_id, "reward"))  # gold
    save["maps"][town_id]["coins"] += reward
    save["privateState"]["rewardedMissions"] += [mission_id]

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
    place_popped_unit = len(args) > 4
    if place_popped_unit:
      unit_x = args[4]
      unit_y = args[5]
      unit_frame = args[6]  # unknown use
    print("Pop", str(get_name_from_item_id(unit_id)), "from",
          f"({b_x},{b_y}).")
    map = save["maps"][town_id]
    # Remove unit from building
    for item in map["items"]:
      if item[1] == b_x and item[2] == b_y:
        if len(item) < 7:
          break
        item[6].remove(unit_id)
        break
    if place_popped_unit:
      # Spawn unit outside
      collected_at_timestamp = timestamp_now()
      level = 0  # TODO
      orientation = 0
      map["items"] += [[
        unit_id, unit_x, unit_y, orientation, collected_at_timestamp, level
      ]]

  elif cmd == Constant.CMD_RT_LEVEL_UP:
    new_level = args[0]
    print("Level Up!:", new_level)
    map = save["maps"][
      0]  # TODO : xp must be general, since theres no given town_id
    map["level"] = args[0]
    current_xp = map["xp"]
    min_expected_xp = get_xp_from_level(max(0, new_level - 1))
    map["xp"] = max(
      min_expected_xp, current_xp
    )  # try to fix problems with not counting XP... by keeping up with client-side level counting
    current_cash = save["playerInfo"]["cash"]
    current_cash += 1
    save["playerInfo"]["cash"] = current_cash

  elif cmd == Constant.CMD_RT_PUBLISH_SCORE:
    new_xp = args[0]
    print("xp set to", new_xp)
    map = save["maps"][
      0]  # TODO : xp must be general, since theres no given town_id
    map["xp"] = new_xp
    map["level"] = get_level_from_xp(new_xp)

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
    exp = expansion_prices[len(map["expansions"]) - 1]
    if resource == "gold":
      to_substract = exp["coins"]
      save["maps"][town_id]["coins"] = max(
        save["maps"][town_id]["coins"] - to_substract, 0)
    elif resource == "cash":
      to_substract = exp["cash"]
      save["playerInfo"]["cash"] = max(
        save["playerInfo"]["cash"] - to_substract, 0)
    # Add expansion
    map["expansions"].append(land_id)

  elif cmd == Constant.CMD_NAME_MAP:
    town_id = int(args[0])
    new_name = args[1]
    print(f"Map name changed to '{new_name}'.")
    save["playerInfo"]["map_names"][town_id] = new_name

  elif cmd == Constant.CMD_EXCHANGE_CASH:
    town_id = args[0]
    print("Exchange cash -> coins.")
    save["playerInfo"]["cash"] = max(
      save["playerInfo"]["cash"] - 5,
      0)  #maybe make function for editing resources
    save["maps"][town_id]["coins"] += 2500

  elif cmd == Constant.CMD_STORE_ITEM:
    x = args[0]
    y = args[1]
    town_id = int(args[2])
    item_id = args[3]
    print("Store", str(get_name_from_item_id(item_id)), "from", f"({x},{y})")
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
  elif cmd == Constant.CMD_BUY_STORED_ITEM_CASH:
    town_id = args[0]
    unit_id = args[1]
    cost = args[2]
    print("Bought", str(get_name_from_item_id(unit_id)), "for", f"{cost}")
    #substract cash
    save["playerInfo"]["cash"] -= cost
    #save in gift
    length = len(save["privateState"]["gifts"])
    if length <= unit_id:
      for i in range(unit_id - length + 1):
        save["privateState"]["gifts"].append(0)
      save["privateState"]["gifts"][unit_id] += 1
      print("Added Hero ID=" + str(unit_id))
  elif cmd == Constant.CMD_PLACE_GIFT or cmd == Constant.CMD_PLACE_STORED_ITEM:
    item_id = args[0]
    x = args[1]
    y = args[2]
    town_id = args[3]  #unsure, both 3 and 4 seem to stay 0
    args[4]  #unknown yet
    print("Add", str(get_name_from_item_id(item_id)), "at", f"({x},{y})")
    items = save["maps"][town_id]["items"]
    orientation = 0  #TODO
    collected_at_timestamp = timestamp_now()
    level = 0
    items += [[item_id, x, y, orientation, collected_at_timestamp,
               level]]  #maybe make function for adding items
    save["privateState"]["gifts"][item_id] -= 1
    if save["privateState"]["gifts"][
        item_id] == 0:  #removes excess zeros at end if necessary
      while (save["privateState"]["gifts"][-1] == 0):
        save["privateState"]["gifts"].pop()

  elif cmd == Constant.CMD_SELL_GIFT:
    item_id = args[0]
    town_id = args[1]
    print("Gift", str(get_name_from_item_id(item_id)), "sold on town:",
          town_id)
    gifts = save["privateState"]["gifts"]
    gifts[item_id] -= 1
    if gifts[item_id] == 0:  #removes excess zeros at end if necessary
      while (len(gifts) != 0 and gifts[-1] == 0):
        gifts.pop()
    price_multiplier = -0.05
    if get_attribute_from_item_id(item_id, "cost_type") != "c":
      apply_cost(save["playerInfo"], save["maps"][town_id], item_id,
                 price_multiplier)

  elif cmd == Constant.CMD_ACTIVATE_DRAGON:
    currency = args[0]
    print("Dragon nest activated.")
    if currency == 'c':
      save["playerInfo"]["cash"] = max(int(save["playerInfo"]["cash"] - 50), 0)
    elif currency == 'g':
      map = save["maps"]
      map[0]["coins"] = max(int(map[0]["coins"] - 100000), 0)
    save["privateState"]["dragonNestActive"] = 1
    save["privateState"]["timeStampTakeCare"] = -1  # remove timer if any

  elif cmd == Constant.CMD_DESACTIVATE_DRAGON:
    print("Dragon nest deactivated.")
    pState = save["privateState"]
    pState["dragonNestActive"] = 0
    # reset step and dragon numbers
    pState["stepNumber"] = 0
    pState["dragonNumber"] = 0
    pState["timeStampTakeCare"] = -1  # remove timer if any

  elif cmd == Constant.CMD_NEXT_DRAGON_STEP:
    unknown = args[0]
    print("Dragon step increased.")
    pState = save["privateState"]
    pState["stepNumber"] += 1
    pState["timeStampTakeCare"] = timestamp_now()

  elif cmd == Constant.CMD_NEXT_DRAGON:
    print("Dragon step reset and dragonNumber increased.")
    pState = save["privateState"]
    pState["stepNumber"] = 0
    pState["dragonNumber"] += 1
    pState["timeStampTakeCare"] = -1  # remove timer

  elif cmd == Constant.CMD_DRAGON_BUY_STEP_CASH:
    price = args[0]
    print("Buy dragon step with cash.")
    save["playerInfo"]["cash"] = max(int(save["playerInfo"]["cash"] - price),
                                     0)
    save["privateState"]["timeStampTakeCare"] = -1  # remove timer

  elif cmd == Constant.CMD_RIDER_BUY_STEP_CASH:
    price = args[0]
    print("Buy rider step with cash.")
    save["playerInfo"]["cash"] = max(int(save["playerInfo"]["cash"] - price),
                                     0)
    save["privateState"]["riderTimeStamp"] = -1  # remove timer

  elif cmd == Constant.CMD_NEXT_RIDER_STEP:
    print("Rider step increased.")
    pState = save["privateState"]
    pState["riderStepNumber"] += 1
    pState["riderTimeStamp"] = timestamp_now()

  elif cmd == Constant.CMD_SELECT_RIDER:
    number = int(args[0])
    pState = save["privateState"]
    if number == 1 or number == 2 or number == 3:
      pState["riderNumber"] = number
      print("Rider", number, "Selected.")
    else:
      pState["riderNumber"] = 0
      pState["riderStepNumber"] = 0
      pState["riderTimeStamp"] = -1  # remove timer
      print("Rider reset.")

  elif cmd == Constant.CMD_ORIENT:
    x = args[0]
    y = args[1]
    new_orientation = args[2]
    town_id = args[3]
    print("Item at", f"({x},{y})", "changed to orientation", new_orientation)
    map = save["maps"][town_id]
    for item in map["items"]:
      if item[1] == x and item[2] == y:
        item[3] = new_orientation
        break

  elif cmd == Constant.CMD_MONSTER_BUY_STEP_CASH:
    price = args[0]
    print("Buy monster step with cash.")
    save["playerInfo"]["cash"] = max(int(save["playerInfo"]["cash"] - price),
                                     0)
    save["privateState"]["timeStampTakeCareMonster"] = -1  # remove timer

  elif cmd == Constant.CMD_ACTIVATE_MONSTER:
    currency = args[0]
    print("Monster nest activated.")
    if currency == 'c':
      save["playerInfo"]["cash"] = max(int(save["playerInfo"]["cash"] - 50), 0)
    elif currency == 'g':
      map = save["maps"]
      map[0]["coins"] = max(int(map[0]["coins"] - 100000), 0)
    save["privateState"]["monsterNestActive"] = 1
    save["privateState"][
      "timeStampTakeCareMonster"] = -1  # remove timer if any

  elif cmd == Constant.CMD_DESACTIVATE_MONSTER:  # cmd called too late
    print("Monster nest deactivated.")
    pState = save["privateState"]
    pState["monsterNestActive"] = 0
    pState["stepMonsterNumber"] = 0
    pState["MonsterNumber"] = 0
    pState["timeStampTakeCareMonster"] = -1  # remove timer if any

  elif cmd == Constant.CMD_NEXT_MONSTER_STEP:
    print("Monster Step increased.")
    pState = save["privateState"]
    pState["stepMonsterNumber"] += 1
    pState["timeStampTakeCareMonster"] = timestamp_now()

  elif cmd == Constant.CMD_NEXT_MONSTER:
    print("Monster Step reset and Monster Number increased.")
    pState = save["privateState"]
    pState["stepMonsterNumber"] = 0
    pState["monsterNumber"] += 1
    pState["timeStampTakeCareMonster"] = -1  # remove timer

  elif cmd == Constant.CMD_WIN_BONUS:
    coins = args[0]
    town_id = args[1]
    hero = args[2]
    claimId = args[3]
    cash = args[4]

    print("Claiming Win Bonus")
    map = save["maps"][town_id]

    if cash != 0:
      save["playerInfo"]["cash"] = save["playerInfo"]["cash"] + cash
      print("Added " + str(cash) + " Cash to players balance")

    if coins != 0:
      map["coins"] = map["coins"] + coins
      print("Added " + str(coins) + " Gold to players balance")

    if hero != 0:
      length = len(save["privateState"]["gifts"])
      if length <= hero:
        for i in range(hero - length + 1):
          save["privateState"]["gifts"].append(0)
      save["privateState"]["gifts"][hero] += 1
      print("Added Hero ID=" + str(hero))

    pState = save["privateState"]
    pState["bonusNextId"] = claimId + 1
    pState["timestampLastBonus"] = timestamp_now()

  elif cmd == Constant.CMD_ADMIN_ADD_ANIMAL:
    subcatFunc = str(args[0])
    toBeAdded = int(args[1])
    print("Added", toBeAdded,
          get_item_from_subcat_functional(subcatFunc)["name"])

    # TODO
    oAnimals: dict = save["privateState"]["arrayAnimals"]
    oAnimals[subcatFunc] = toBeAdded + (oAnimals[subcatFunc]
                                        if subcatFunc in oAnimals else 0)

  elif cmd == Constant.CMD_GRAVEYARD_BUY_POTIONS:
    # no args
    print("Graveyard buy potion")
    # info from config
    graveyard_potions = get_game_config()["globals"]["GRAVEYARD_POTIONS"]
    amount = graveyard_potions["amount"]
    price_cash = graveyard_potions["price"]["c"]
    # pay
    save["playerInfo"]["cash"] = max(
      int(save["playerInfo"]["cash"] - price_cash), 0)
    # add potion
    save["privateState"]["potion"] += amount

  elif cmd == Constant.CMD_RESURRECT_HERO:
    unit_id = args[0]
    x = args[1]
    y = args[2]
    town_id = args[3]
    bool_used_potion = len(args) > 4 and args[4] == '1'
    print("Resurrect", str(get_name_from_item_id(unit_id)), "from graveyard")
    # If Payed whit potions , if not then its working just fine
    if bool_used_potion:
      quantity = 1
      save["privateState"]["potion"] = max(
        int(save["privateState"]["potion"] - quantity), 0)
    collected_at_timestamp = timestamp_now()
    level = 0  # TODO
    orientation = 0
    save["maps"][town_id]["items"] += [[
      unit_id, x, y, orientation, collected_at_timestamp, level
    ]]

  elif cmd == Constant.CMD_BUY_SUPER_OFFER_PACK:
    town_id = args[0]
    unknown2 = args[1]  # this is probably the super offer pack ID?
    items = args[2]
    cash_used = args[3]

    map = save["maps"][town_id]

    item_array = items.split(',')
    for item in item_array:
      item_id = int(item)
      length = len(save["privateState"]["gifts"])
      if length <= item_id:
        for i in range(item_id - length + 1):
          save["privateState"]["gifts"].append(0)
      save["privateState"]["gifts"][item_id] += 1

    save["playerInfo"]["cash"] = max(
      save["playerInfo"]["cash"] - cash_used,
      0)  #maybe make function for editing resources
    print(f"Used {cash_used} cash to buy super offer pack!")

  elif cmd == Constant.CMD_SET_STRATEGY:
    strategy_type = args[0]
    type_name = get_strategy_type(strategy_type)
    save["privateState"]["strategy"] = strategy_type
    print(f"Set defense strategy type to {type_name}")

  elif cmd == Constant.CMD_START_QUEST:
    quest_id = args[0]
    town_id = args[1]
    print(f"Start quest {quest_id}")
  elif cmd == Constant.CMD_END_QUEST:
    # Extract the necessary information from the `args` list using JSON deserialization
    data = json.loads(args[0])
    town_id = data["map"]
    gold_gained = data["resources"]["g"]
    xp_gained = data["resources"]["x"]
    win = data["win"] == 1
    lost_units = data["units"][0]
    duration_sec = data["duration"]
    voluntary_end = data["voluntary_end"] == 1
    quest_id = data["quest_id"]
    item_rewards = data["item_rewards"] if "item_rewards" in data else None
    activators_left = data[
      "activators_left"] if "activators_left" in data else None
    difficulty = data["difficulty"]  #Assuming the player is on first diffculty

    # Debug print statement
    print("ended successfuly")

    # Determine the current quest rank
    quest_rank = save["privateState"]["questsRank"].get(quest_id, 0)

    # Update the player's resources based on whether the quest was won or lost
    if win:
      if difficulty >= quest_rank:
        # Increase the player's coins and XP by the appropriate amounts

        # check if the quest is already in the json file
        if quest_id in save["privateState"]["questsRank"]:
          # Check if the new difficulty level is higher than the existing one
          if difficulty >= save["privateState"]["questsRank"][quest_id]:
            #update the new diffculty quest_id:diffculty
            print("Good Job Hero !")
            save["maps"][town_id]["coins"] += int(gold_gained)
            save["maps"][town_id]["xp"] += int(xp_gained)
            save["privateState"]["questsRank"][quest_id] = difficulty
            unlockedQuestIndex = save["privateState"]["unlockedQuestIndex"]
            save["privateState"]["unlockedQuestIndex"] = max(
              unlockedQuestIndex + 1,
              save["privateState"]["unlockedQuestIndex"], 0)
            print("Updated UnlockedQuestIndex")
          #the new difficulty level is lower than the existing one
          else:
            print("Weak coward looking for free gold")
            print("Nothing is changed")
            save["maps"][town_id]["coins"] += int(gold_gained) / 4
            save["maps"][town_id]["xp"] += int(xp_gained) / 4
        # check the quest is not in the json file
        else:
          print("Discovering New Island, Great Job Hero !")
          save["privateState"]["questsRank"][quest_id] = difficulty
          unlockedQuestIndex = save["privateState"]["unlockedQuestIndex"]
          save["privateState"]["unlockedQuestIndex"] = max(
            unlockedQuestIndex + 1, save["privateState"]["unlockedQuestIndex"],
            0)
          print("Updated UnlockedQuestIndex")
    else:
      # Print a message indicating why the quest ended
      if voluntary_end == 1 or win == 0:
        print("Ended Voluntary/Lost")

    # Update the player's inventory and the number of activators left for the quest (if applicable)
    if item_rewards is not None:
      # If the quest has item rewards, add them to the player's inventory
      for item_id, quantity in item_rewards.items():
        item_id = int(item_id)  # Convert item_id to an integer
        length = len(save["privateState"]["gifts"])
        if length <= item_id:
          for i in range(item_id - length + 1):
            save["privateState"]["gifts"].append(0)
        save["privateState"]["gifts"][item_id] += quantity
        print("Added " + str(quantity) + " Hero(s) with ID=" + str(item_id))
    if activators_left is not None:
      # If the quest has activators left, update the number of activators left for the quest
      save["maps"][quest_id]["activatorsLeft"] = activators_left
    # Print a message indicating whether any units were lost during the quest
    #todo
    # Print a message indicating that the quest has ended
    print(f"Ended quest {quest_id}.")
  elif cmd == Constant.CMD_ATTACK_PLAYER:
    victim = args[0]
    print(f"Attacking {victim}")

  elif cmd == Constant.CMD_END_ATTACK:
    # Extract the necessary information from the `args` list using JSON deserialization
    data = json.loads(args[0])

    duration = data["duration"]
    resources_victim = data["resources_victim"]["g"]
    townhall_gold = data["townhall_gold"]
    win = data["win"]
    victim_units = data["victim_units"]  #not needed
    honor = data["honor"]  #not needed
    attacker = data["attacker"]  #not needed (develop losing units first)
    attacker_units = data["attacker_units"]
    voluntary_end = data["voluntary_end"]
    victim = data["victim"]  #not needed
    gold_gained = data["resources"]["g"]
    xp_gained = data["resources"]["x"]

    # Debug print statement
    print("ended successfuly")
    # save attack

    # Update the player's resources based on whether the quest was won or lost
    if win == 1:
      # Increase the player's coins and XP by the appropriate amounts
      save["maps"][0]["coins"] += int(gold_gained)
      save["maps"][0]["xp"] += int(xp_gained)

    else:
      # Print a message indicating why the quest ended
      print("ended voluntary")
    print(f"Ended player {victim}.")

  elif cmd == Constant.CMD_COLLECT_MONDAY_BONUS:
    current_time = time.time()
    # Check if the key exists in the privateState dictionary
    if "timestampLastMondayBonus" not in save["privateState"]:
      save["privateState"]["timestampLastMondayBonus"] = current_time
      last_bonus_time = current_time
    else:
      last_bonus_time = save["privateState"]["timestampLastMondayBonus"]
      print("timestamp exists")
      last_bonus_time = save["privateState"]["timestampLastMondayBonus"]
      if current_time - last_bonus_time >= 7 * 24 * 60 * 60:
        save["privateState"]["timestampLastMondayBonus"] = current_time
        print("Time Updated")
        town_id = 0
        currency = args[0]
        reward_value = int(args[1])
        if currency == 'c':
          save["playerInfo"]["cash"] += reward_value
        elif currency == 'g':
          save["maps"][town_id]["coins"] += reward_value
        elif currency == 'u':
          length = len(save["privateState"]["gifts"])
          if length <= reward_value:
            for i in range(reward_value - length + 1):
              save["privateState"]["gifts"].append(0)
          save["privateState"]["gifts"][reward_value] += 1
          print("Added Hero ID=" + str(reward_value))
      else:
        print("Bonus already collected today")
  elif cmd == Constant.CMD_ADD_COLLECTABLE:
    collection_id = args[0]
    collectible_id = args[1]
    # TODO

  elif cmd == Constant.CMD_COLLECT_TREASURE:
    current_time = time.time()
    last_treasure_time = save['maps'][0]['timestampLastTreasure']
    if current_time - last_treasure_time >= 14400:
      # Increment the idCurrentTreasure by 1
      save['maps'][0]['idCurrentTreasure'] += 1
      # Update the timestamp of the last treasure to the current time
      save['maps'][0]['timestampLastTreasure'] = current_time

  else:
    print(f"Unhandled command '{cmd}' -> args", args)
    return
