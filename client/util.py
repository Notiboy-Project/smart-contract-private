import base64
import sys
from algosdk import account, mnemonic, logic
from algosdk import encoding
from algosdk.v2client import algod

NOTIBOY_ADDR = "HZ57J3K46JIJXILONBBZOHX6BKPXEM2VVXNRFSUED6DKFD5ZD24PMJ3MVA"
DAPP_NAME = "mydapp"
APP_ID = 1505
MAIN_BOX = "notiboy"


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
        if byte_key.decode() in ["index", DAPP_NAME, "msgcount", "apps"]:
            formatted_key = byte_key.decode()
        else:
            formatted_key = int.from_bytes(byte_key, "big")
        if value['type'] == 1:
            # byte string
            byte_value = base64.b64decode(value['bytes'])
            if byte_key.decode() in ["index", "msgcount", "apps"]:
                formatted_value = int.from_bytes(byte_value, "big")
            else:
                try:
                    formatted_value = encoding.encode_address(byte_value)
                except Exception:
                    formatted_value = byte_value.decode()
            formatted[formatted_key] = formatted_value
        else:
            # integer
            formatted[formatted_key] = value['uint']
    return formatted


def debug():
    import ipdb;
    return ipdb.set_trace


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
            if formatted_key == "dappcount":
                byte_value = base64.b64decode(value['bytes'])
                formatted_value = int.from_bytes(byte_value, "big")
            else:
                try:
                    formatted_value = encoding.encode_address(byte_value[:32]) + ":" + str(int.from_bytes(
                        byte_value[33:], "big"))
                    print("Total length of value is ", len(byte_value))

                    # if len(byte_value) == 67 and byte_value[66:67].decode() == "v":
                    #     print("{} is verified".format(formatted_key))
                    #     formatted_value = formatted_value + ":verfied"
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


def generate_algorand_keypair(overwrite, fname, sandbox):
    if sandbox:
        private_key = "Fa6ctT9AZhWWtnL5/ASqqy4HNq8kCz1UWwbHGRAiGGL16CyzvQTyGfwoT9HwWRr7bJFbwUAfYpjdXjg3cBueYQ=="
        mnemonic_string = "simple vocal hard wall gravity tide surface eight pull oil fruit basic word assist answer still bright prevent coil speak loan clean wild able minimum"
        if mnemonic_string != "":
            private_key = mnemonic.to_private_key(mnemonic_string)
        address = "ZIC23NIY7IJVIQ5NEWXV5B7TIHNV4ZEHGT2IHYEMJSDEYV75DB4DNO67CY"

        return private_key, address

    if overwrite:
        private_key, address = account.generate_account()
        with open(fname, "w") as f:
            f.write('{}\n{}\n'.format(address, private_key))
    else:
        with open(fname, "r") as f:
            lns = f.readlines()
            address = lns[0].rstrip('\n')
            private_key = lns[1].rstrip('\n')

    print("My address: {}".format(address))
    print("My private key: {}".format(private_key))

    if overwrite:
        sys.exit()

    return private_key, address


def get_algod_client(private_key, my_address):
    # sandbox
    algod_address = "http://localhost:4001"
    # algo-explorer
    # algod_address = "https://node.testnet.algoexplorerapi.io"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(algod_token, algod_address)
    account_info = algod_client.account_info(my_address)
    print("Account balance: {} microAlgos\n".format(account_info.get('amount')))

    return algod_client
