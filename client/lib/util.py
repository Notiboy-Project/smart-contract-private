import base64
import sys
from datetime import datetime

from algosdk import account, mnemonic, logic
from algosdk import encoding
from algosdk.v2client import algod
from algosdk.future import transaction
from collections import OrderedDict
from client.lib.constants import *


# read user local state
def read_local_state(client, addr, app_id):
    results = client.account_info(addr)

    for local_state in results["apps-local-state"]:
        if local_state["id"] == app_id:
            if "key-value" not in local_state:
                return {}
            uod = format_local_state(local_state["key-value"])
            od = dict(sorted(uod.items()))
            for k, v in od.items():
                print(k, v)
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
            formatted_key = str(int.from_bytes(byte_key, "big"))
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
            if formatted_key in ["index"]:
                byte_value = base64.b64decode(value['bytes'])
                formatted_value = int.from_bytes(byte_value, "big")
            else:
                try:
                    formatted_value = encoding.encode_address(byte_value[:32]) + ":" + str(int.from_bytes(
                        byte_value[33:], "big"))

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


def read_global_state_key(client, app_id, key):
    app = client.application_info(app_id)
    global_state = app['params']['global-state'] if "global-state" in app['params'] else []
    return format_global_state(global_state).get(key)


def is_zero_value(data):
    if int.from_bytes(data, "big") == 0:
        return True
    if data.strip(b'0') == b'':
        return True
    return False


def read_user_box(client, app_id, box_name):
    print("USER BOX STORAGE")
    data = client.application_box_by_name(app_id, box_name)
    value = data['value']
    value = base64.b64decode(value)
    chunks = [value[i:i + MAX_USER_BOX_MSG_SIZE] for i in range(0, len(value), MAX_USER_BOX_MSG_SIZE)]

    for idx, chunk in enumerate(chunks):
        if is_zero_value(chunk):
            continue
        chunk_items = [chunk[:8], chunk[8:16], chunk[16:]]
        new_l = []
        try:
            ts = int(int.from_bytes(chunk_items[0], "big"))
            x_ts = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            new_l.append(x_ts)
            new_l.append(str(int.from_bytes(chunk_items[1], "big")))
            new_l.append(chunk_items[2].decode('utf-8').rstrip("0"))
        except Exception as err:
            debug()()

        to_print = ":".join(new_l)
        if to_print.strip() != '':
            print("value at index {} is {}".format(idx, to_print))


def read_box(client, app_id, box_name):
    print("MAIN BOX STORAGE")
    data = client.application_box_by_name(app_id, box_name)
    value = data['value']
    value = base64.b64decode(value)
    chunks = [value[i:i + MAX_MAIN_BOX_MSG_SIZE] for i in range(0, len(value), MAX_MAIN_BOX_MSG_SIZE)]

    for idx, chunk in enumerate(chunks):
        if is_zero_value(chunk):
            continue
        chunk_items = [chunk[:10].lstrip(b':'), chunk[10:18], chunk[18:22], chunk[22]]
        new_l = []
        try:
            new_l.append(chunk_items[0].decode('utf-8'))
            new_l.append(str(int.from_bytes(chunk_items[1], "big")))
            new_l.append(str(int.from_bytes(chunk_items[2][:4], "big")))
            new_l.append(chr(chunk_items[3]))
        except Exception as err:
            debug()()

        to_print = ":".join(new_l)
        if to_print.strip() != '':
            print("value at index {} is {}".format(idx, to_print))


def generate_noop_txns(num, sender, params, index, boxes, foreign_apps):
    txns = []
    for idx in range(num):
        txns.append(
            transaction.ApplicationNoOpTxn(sender, params, index, note="txn{}".format(idx), boxes=boxes,
                                           foreign_apps=foreign_apps)
        )

    return txns


def get_signed_grp_txn(*txns, private_key):
    gid = transaction.calculate_group_id(txns)
    transaction.assign_group_id(txns)
    signed_group = []
    for idx, _ in enumerate(txns):
        txns[idx].gid = gid
        signed_group.append(
            txns[idx].sign(private_key)
        )

    return signed_group


def print_logs(transaction_response):
    if transaction_response.get('logs') is None:
        return
    for idx, log in enumerate(transaction_response['logs']):
        print("LOG{}".format(idx), base64.b64decode(log))


def get_sandbox_creds(kind):
    if kind == "user":
        mnemonic_string = "music snack pool plastic glide dress term own bottom addict one same rebel lawn pave symptom there account recipe use vintage crouch below above quality"
        private_key = mnemonic.to_private_key(mnemonic_string)
        address = "AAVUPELO5ZCBDA3DD3G7ZDZ64BSEOOE3G7ZBOMR7DKI3YIBXLYEC3EATQA"
    elif kind == "creator":
        mnemonic_string = "sphere deliver tent capital net run cube horror volcano damp shine place include venture pond cook cross drill material narrow lava athlete human above battle"
        private_key = mnemonic.to_private_key(mnemonic_string)
        address = "EVYC4CFP533BRC26OLGJEWJJ4SDB5JZJPNFPOZ7R56QUENTTUDQDLNJGTM"
    elif kind == "notiboy":
        mnemonic_string = "image such scheme erase ethics else coach ensure fox goose skin share mutual fury elevator dice snap outer purpose forward possible tree reunion above topic"
        private_key = mnemonic.to_private_key(mnemonic_string)
        address = "3KOQUDTQAYKMXFL66Q5DS27FJJS6O3E2J3YMOC3WJRWNWJW3J4Q65POKPI"

    return private_key, address


def generate_creds(overwrite, fname):
    if overwrite:
        private_key, address = account.generate_account()
        with open(fname, "w") as f:
            f.write('{}\n{}\n'.format(address, private_key))
    else:
        with open(fname, "r") as f:
            lns = f.readlines()
            address = lns[0].rstrip('\n')
            private_key = lns[1].rstrip('\n')

    print("{} address: {}".format(fname, address))
    print("{} private key: {}".format(fname, private_key))

    return private_key, address


def generate_user_algorand_keypair(overwrite, fname, sandbox):
    if sandbox:
        return get_sandbox_creds("user")

    return generate_creds(overwrite, fname)


def generate_creator_algorand_keypair(overwrite, fname, sandbox):
    if sandbox:
        return get_sandbox_creds("creator")

    return generate_creds(overwrite, fname)


def generate_notiboy_algorand_keypair(overwrite, fname, sandbox):
    if sandbox:
        return get_sandbox_creds("notiboy")

    return generate_creds(overwrite, fname)


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


def teal_debug(client, group_txn):
    # debug()
    drr = transaction.create_dryrun(client, group_txn)

    filename = "dryrun.msgp"
    with open(filename, "wb") as f:
        import base64
        f.write(base64.b64decode(encoding.msgpack_encode(drr)))
