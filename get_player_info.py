from sessions import session, neighbors
from engine import timestamp_now

def get_player_info(USERID):
    # Update last logged in
    ts_now = timestamp_now()
    session(USERID)["playerInfo"]["last_logged_in"] = ts_now
    # player
    player_info = {
        "result": "ok",
        "processed_errors": 0,
        "timestamp": ts_now,
        "playerInfo": session(USERID)["playerInfo"],
        "map": session(USERID)["maps"][0],
        "privateState": session(USERID)["privateState"],
        "neighbors": neighbors(USERID)
    }
    return player_info

# old_player = {
#     # - core.Base
#     "result": "ok", # "error"
#     "processed_errors": 1,
#     "timestamp": 12345,
#     "playerInfo": {
#         "pid": 1000,
#         "name": "AcidCaos",
#         "pic": "http://localhost:5050/profile/image.jpg",
#         "cash": 222,
#         "coins": 888,
#         "xp": 300,
#         "level": 12,
#         "completed_tutorial": 0,
#         "default_map": 0,
#         "map_names": ["Empire 1", "Emipre 2", "Village 3"],
#         "map_sizes": [0, 0, 0],
#         "stone": 22,
#         "wood": 33,
#         "food": 55,
#         "world_id": None,
#         "sp_ref_uid": 1111,
#         "sp_ref_cat_install": "ts",
#         "last_logged_in": 1330436105
#     },
#     # - managers.PlayerStatus
#     "map": {
#         "id": 0, # TODO compared with 0
#         "expansions": [13], # [7,8,9,12,14,17,18,19], # [0]=13 ???
#         "timestamp": 12345,
#         "coins": 888,
#         "xp": 100,
#         "level": 12,
#         "stone": 40,
#         "wood": 41,
#         "food": 42,
#         "race": "h",
#         "skin": 0,
#         "idCurrentTreasure": 222,
#         "timestampLastTreasure": 12345,
#         "resourcesTraded": {},
#         "receivedAssists": {},
#         "increasedPopulation": 0,
#         "expirableUnitsTime": {},
#         "items": [
#             # [id, x, y, orientation, collected_at, level, units:Array, attrs:Obj],
#             [26, 50, 50, 0, 0, 0], # Townhall
#             # [1, 6, 6, 0, 0, 0, [], {}], # House I
#         ],
#     },
#     "privateState": {
#         "gifts": [],
#         "neighborAssists": {},
#         "completedMissions": [6, 1, 8, 2, 3, 4, 11, 7, 9],
#         "rewardedMissions": [6, 1, 8, 2, 3, 4],
#         "bonusNextId": 3,
#         "timestampLastBonus": 1330448531,
#         "attacksSent": [
#             {
#                 "time": "1330432950",
#                 "victim_id": "1111",
#                 "description": {
#                     "townhall_gold": 0,
#                     "duration": 774,
#                     "honor": 6,
#                     "victim_units": [
#                         [291, 11, 22, 8],
#                     ],
#                     "attacker_units": [
#                         [575, 2, 0, 0],
#                         [653, 2, 1, 1],
#                     ],
#                     "win": 0,
#                     "resources_victim": {"g": 391},
#                     "resources": {"x": 135, "g": 200},
#                     "voluntary_end": 1,
#                     "oponent": {
#                         "gold": "34062",
#                         "user_id": "1111",
#                         "pic": "",
#                         # there might be more values
#                     }
#                     # there might be more values
#                 }
#                 # there might be more values
#             }
#         ],
#         "unlockedEarlyBuildings": {},
#         "potion": 0,
#         "kompuSpells": 0,
#         "kompuLastTimeStamp": 1,
#         "kompuSteps": [],
#         "kompuCompleted": [],
#         "lastUpgrades": [],
#         "unlockedSkins": {},
#         "unlockedQuestIndex": 0,
#         "questsRank": {},
#         "magics": {},
#         "mana": 777,
#         "boughtUnits": [],
#         "unitCollectionsCompleted": [],
#         "dragonNumber": 0,
#         "stepNumber": 1,
#         "timeStampTakeCare": 1330446028,
#         "dragonNestActive": 1,
#         "monsterNumber": 0,
#         "stepMonsterNumber": 5,
#         "timeStampTakeCareMonster": 1330446028,
#         "monsterNestActive": 1,
#         "riderNumber": 0,
#         "riderStepNumber": 0,
#         "riderTimeStamp": "1330446028",
#         "timeStampHeavySiegePeriod": 0,
#         "timeStampHeavySiegeAttack": 0,
#         "timeStampDartsReset": 0,
#         "timeStampDartsNewFree": 0,
#         "dartsBalloonsShot": [],
#         "dartsRandomSeed": 10000000000001,
#         "dartsHasFree": True,
#         "dartsGotExtra": True,
#         "countTimePacket": [],
#         "infoShowed": [],
#         "teams": {
#             "tournament": None, # if(!(this.privateState["teams"][Config.TEAM_TOURNAMENT] is Array))
#         },
#         # there might be more values
#     },
#     "neighbors": [
#         {
#             "pid": 1111,
#             "name": "AcidCaos",
#             "pic": "http://localhost:5050/profile/image.jpg",
#             "cash": "222",
#             "coins": "888",
#             "xp": str(get_xp_from_level(12)),
#             "level": "12",
#             "completed_tutorial": "31",
#             "default_map": "0",
#             "map_names": ["Empire 1", "Emipre 2", "Village 3"],
#             "map_sizes": [9, 3, 0],
#             "stone": "22",
#             "wood": "33",
#             "food": "55",
#             "world_id": None,
#             "sp_ref_uid": "1111",
#             "sp_ref_cat_install": "ts",
#             "last_logged_in": "1330436105"
#         }
#     ]
# }
