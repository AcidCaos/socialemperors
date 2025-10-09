import json

__SERVER_CONFIG = {}
def initialize(config_path):
	try:
		global __SERVER_CONFIG
		__SERVER_CONFIG = json.load(open(config_path, 'r', encoding='utf-8'))
		print(f" * Server configured successfully")
	except:
		print(" * Server configuration file is corrupted\n   the server cannot start!")
		exit(0)

def get_server_config():
	return __SERVER_CONFIG

print(" [+] Loading Server configuration")
initialize("server_config.json")