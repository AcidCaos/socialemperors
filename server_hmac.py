import hmac
import hashlib
import json

# SPECIAL THANKS TO: wireframe_0
_SERVER_KEY = "3m0d3pwiupoetn7ysa02"

def hash_(payload, key = _SERVER_KEY):
	return hmac.new(key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()

def construct_hash_and_payload(payload, key = _SERVER_KEY):
	payload = json.dumps(payload)
	return f"{hash_(payload, key).hex()};{payload}"

def check_hmac(payload):
	hmac_hash = payload[:payload.index(";")]
	data = payload[payload.index(";")+1:]
	return json.loads(data), hash_(data).hex() == hmac_hash