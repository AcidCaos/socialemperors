import json
import jsonpatch

original = json.load(open("./config/game_config_20120826.json", 'r'))
patched = json.load(open("./config/patched_config.json", 'r'))

patch = jsonpatch.make_patch(original, patched)

print(str(patch))
