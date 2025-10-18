import json

from sessions import session, save_session
from get_game_config import get_game_config, get_level_from_xp, get_name_from_item_id, get_attribute_from_mission_id, get_xp_from_level, get_attribute_from_item_id, get_item_from_subcat_functional
from constants import Constant
from engine import *



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

def do_command(save, cmd, args, gameversion):
    # print (" [+] COMMAND: ", cmd, "(", args, ") -> ", sep='', end='')

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

    else:
        print(f"Unhandled command '{cmd}' -> args", args)
        return
    
