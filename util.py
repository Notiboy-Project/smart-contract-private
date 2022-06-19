import base64

from algosdk import encoding


# read user local state
def read_local_state(client, addr, app_id):
    results = client.account_info(addr)
    # import ipdb;
    # ipdb.set_trace()
    for local_state in results["apps-local-state"]:
        if local_state["id"] == app_id:
            if "key-value" not in local_state:
                return {}
            return format_local_state(local_state["key-value"])
    return {}


# helper function that formats global state for printing
def format_local_state(state):
    formatted = {}
    for item in state:
        key = item['key']
        value = item['value']
        byte_key = base64.b64decode(key)
        if byte_key.decode() == "index":
            formatted_key = byte_key.decode()
        else:
            formatted_key = int.from_bytes(byte_key, "big")
        if value['type'] == 1:
            # byte string
            byte_value = base64.b64decode(value['bytes'])
            if byte_key.decode() == "index":
                formatted_value = int.from_bytes(byte_value, "big")
            else:
                formatted_value = encoding.encode_address(byte_value)
            formatted[formatted_key] = formatted_value
        else:
            # integer
            formatted[formatted_key] = value['uint']
    return formatted


# helper function that formats global state for printing
def format_global_state(state):
    formatted = {}

    for item in state:
        key = item['key']
        value = item['value']
        formatted_key = base64.b64decode(key).decode('utf-8')
        if value['type'] == 1:
            # byte string
            byte_value = base64.b64decode(value['bytes'])
            if formatted_key == "Creator":
                formatted_value = byte_value.decode()
            else:
                try:
                    formatted_value = encoding.encode_address(byte_value)
                except Exception as err:
                    formatted_value = byte_value.decode()
            formatted[formatted_key] = formatted_value
        else:
            # integer
            formatted[formatted_key] = value['uint']
    return formatted


# helper function to read app global state
def read_global_state(client, app_id):
    app = client.application_info(app_id)
    global_state = app['params']['global-state'] if "global-state" in app['params'] else []
    return format_global_state(global_state)
