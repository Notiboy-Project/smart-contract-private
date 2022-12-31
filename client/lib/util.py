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
    print("LOCAL STATE")
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
        if byte_key.decode() in ["index", DAPP_NAME, "msgcount", "apps", "whoami"]:
            formatted_key = byte_key.decode()
        else:
            formatted_key = str(int.from_bytes(byte_key, "big"))
        if value['type'] == 1:
            # byte string
            byte_value = base64.b64decode(value['bytes'])
            if formatted_key in ["index", "apps"]:
                formatted_value = int.from_bytes(byte_value[:8], "big")
            elif formatted_key in ["msgcount"]:
                formatted_value = 'pvt: ' + str(int.from_bytes(byte_value[:8], "big")) + ', ' + 'pub: ' + str(
                    int.from_bytes(byte_value[9:], "big"))
            elif formatted_key in ["whoami"]:
                new_l = parse_main_box_slot(byte_value)
                formatted_value = ":".join(new_l)
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
    try:
        data = client.application_box_by_name(app_id, box_name)
    except Exception as err:
        print("unable to access box", err)
        return
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


def parse_main_box_slot(chunk):
    chunk_items = [chunk[:10].lstrip(b':'), chunk[10:18], chunk[18:]]
    new_l = []
    try:
        new_l.append(chunk_items[0].decode('utf-8'))
        new_l.append(str(int.from_bytes(chunk_items[1], "big")))
        new_l.append(chunk_items[2].decode('utf-8'))
    except Exception as err:
        debug()()

    return new_l


def read_box(client, app_id, box_name):
    print("MAIN BOX STORAGE")
    try:
        data = client.application_box_by_name(app_id, box_name)
    except Exception as err:
        print("unable to access box", err)
        return

    value = data['value']
    value = base64.b64decode(value)
    chunks = [value[i:i + MAX_MAIN_BOX_MSG_SIZE] for i in range(0, len(value), MAX_MAIN_BOX_MSG_SIZE)]

    for idx, chunk in enumerate(chunks):
        if is_zero_value(chunk):
            continue
        new_l = parse_main_box_slot(chunk)

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


def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response['result'])


def get_sandbox_creds(kind):
    if kind == "user":
        mnemonic_string = "kingdom fetch cement drama winter universe elder animal mechanic torch bonus boy town they boost next tenant enjoy silk guess great park wrist ability few"
        private_key = mnemonic.to_private_key(mnemonic_string)
        address = "CC2TVHRQWPEBR37OX7UT4VTGILEAZR36PH3AZRAL54B67H2RQHGGH7XK4U"
    elif kind == "creator":
        mnemonic_string = "boy mule wait zebra betray also heavy quit dragon again program cliff enact ordinary catch width duty possible organ quit gravity salon veteran abstract public"
        private_key = mnemonic.to_private_key(mnemonic_string)
        address = "D7XPB62RBZODMDRJGQAJ5CKRJCBO6QQ3WOYYTMWD3B7CM4HSVHOHFK4IYQ"
    elif kind == "notiboy":
        mnemonic_string = "random tomorrow leave elder weird alert bounce flag clay tennis hill foil rhythm option swear flip equip junk chase rapid foot wrap chaos able slender"
        private_key = mnemonic.to_private_key(mnemonic_string)
        address = "EBM3V64MKXXIZ4ILJXLGJ6RDIOHXTSJ5HP7GD5MSPL2JWB34CIVE4JSOOE"

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
    print("{} mnemonic: {}".format(fname, mnemonic.from_private_key(private_key)))

    return private_key, address


def generate_user_algorand_keypair(overwrite=False):
    fname = "user-secret.txt"
    if RUNNING_MODE == "sandbox":
        return get_sandbox_creds("user")

    return generate_creds(overwrite, fname)


def generate_creator_algorand_keypair(overwrite=False):
    fname = "creator-secret.txt"
    if RUNNING_MODE == "sandbox":
        return get_sandbox_creds("creator")

    return generate_creds(overwrite, fname)


def generate_notiboy_algorand_keypair(overwrite=False):
    fname = "notiboy-secret.txt"
    if RUNNING_MODE == "sandbox":
        return get_sandbox_creds("notiboy")

    return generate_creds(overwrite, fname)


def get_algod_client(my_address):
    if RUNNING_MODE == "sandbox":
        algod_address = "http://localhost:4001"
    elif RUNNING_MODE == "testnet":
        algod_address = "https://node.testnet.algoexplorerapi.io"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(algod_token, algod_address)
    account_info = algod_client.account_info(my_address)
    if RUNNING_MODE == 'testnet':
        acct_asset_info = algod_client.account_asset_info(my_address, ASA_ASSET)
        assets = acct_asset_info.get('asset-holding').get('amount') / 1000000
        print("Account balance: {} microAlgos, {} USDC\n".format(account_info.get('amount') / 1000000, assets))
    elif RUNNING_MODE == 'sandbox':
        print("Account balance: {} microAlgos\n".format(account_info.get('amount') / 1000000))

    return algod_client


def teal_debug(client, group_txn):
    # debug()
    drr = transaction.create_dryrun(client, group_txn)

    filename = "dryrun.msgp"
    with open(filename, "wb") as f:
        f.write(base64.b64decode(encoding.msgpack_encode(drr)))
