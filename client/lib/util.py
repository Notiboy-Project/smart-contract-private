import base64
import os
import sys
import time
from datetime import datetime

from algosdk import account, mnemonic, logic
from algosdk import encoding
from algosdk.v2client import algod, indexer
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
            elif formatted_key == 'msgcount':
                formatted_value = 'pvt: ' + str(int.from_bytes(byte_value[:8], "big")) + ', ' + 'pub: ' + str(
                    int.from_bytes(byte_value[9:], "big"))
            elif formatted_key == 'optincount':
                formatted_value = 'creator: ' + str(int.from_bytes(byte_value[:8], "big")) + ', ' + 'user: ' + str(
                    int.from_bytes(byte_value[9:], "big"))
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
    print("##########GLOBAL STATE##########")
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
    print("##########USER BOX STORAGE##########")
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
        print("ERROR:", err)

    return new_l


def read_main_box(client, app_id, box_name):
    try:
        data = client.application_box_by_name(app_id, box_name)
    except Exception as err:
        print("unable to access box", err)
        return

    value = data['value']
    value = base64.b64decode(value)
    chunks = [value[i:i + MAX_MAIN_BOX_MSG_SIZE] for i in range(0, len(value), MAX_MAIN_BOX_MSG_SIZE)]

    d = dict()
    for idx, chunk in enumerate(chunks):
        if is_zero_value(chunk):
            continue
        new_l = parse_main_box_slot(chunk)

        to_print = ":".join(new_l)
        d[idx] = to_print

    return d


def get_val_main_box(client, app_id, box_name, key):
    for k, v in read_main_box(client, app_id, box_name).items():
        if key == v[:len(key)]:
            return [k, v]

    return []


def print_main_box(client, app_id, box_name):
    print("##########MAIN BOX STORAGE##########")

    for k, v in read_main_box(client, app_id, box_name).items():
        print("value at index {} is {}".format(k, v))


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
        mnemonic_string = SANDBOX_USER_MNEMONIC
        private_key = mnemonic.to_private_key(mnemonic_string)
        address = SANDBOX_USER_ADDRESS
    elif kind == "creator":
        mnemonic_string = SANDBOX_CREATOR_MNEMONIC
        address = SANDBOX_CREATOR_ADDRESS
        private_key = mnemonic.to_private_key(mnemonic_string)
    elif kind == "notiboy":
        mnemonic_string = SANDBOX_NOTIBOY_MNEMONIC
        private_key = mnemonic.to_private_key(mnemonic_string)
        address = SANDBOX_NOTIBOY_ADDRESS

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
    if RUNNING_MODE == SANDBOX:
        return get_sandbox_creds("user")
    elif RUNNING_MODE == MAINNET:
        return mnemonic.to_private_key(USER_MNEMONIC), USER_ADDR

    return generate_creds(overwrite, fname)


def generate_creator_algorand_keypair(overwrite=False):
    fname = "creator-secret.txt"
    if RUNNING_MODE == SANDBOX:
        return get_sandbox_creds("creator")
    elif RUNNING_MODE == MAINNET:
        return mnemonic.to_private_key(CREATOR_ADDR), CREATOR_ADDR

    return generate_creds(overwrite, fname)


def generate_notiboy_algorand_keypair(overwrite=False):
    fname = "notiboy-secret.txt"
    if RUNNING_MODE == SANDBOX:
        return get_sandbox_creds("notiboy")
    elif RUNNING_MODE == MAINNET:
        return mnemonic.to_private_key(NOTIBOY_MNEMONIC), NOTIBOY_ADDR

    return generate_creds(overwrite, fname)


def get_indexer_client():
    if RUNNING_MODE == TESTNET:
        indexer_address = "https://testnet-idx.algonode.cloud"
    elif RUNNING_MODE == MAINNET:
        indexer_address = "https://mainnet-idx.algonode.cloud"
    indexer_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    return indexer.IndexerClient(indexer_token, indexer_address)


def get_algod_client(my_address):
    if RUNNING_MODE == SANDBOX:
        algod_address = "http://localhost:4001"
    elif RUNNING_MODE == TESTNET:
        algod_address = "https://node.testnet.algoexplorerapi.io"
    elif RUNNING_MODE == MAINNET:
        algod_address = "https://node.algoexplorerapi.io"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(algod_token, algod_address)
    account_info = algod_client.account_info(my_address)

    try:
        # valid only for creator
        acct_asset_info = algod_client.account_asset_info(my_address, ASA_ASSET)
        assets = acct_asset_info.get('asset-holding').get('amount') / 1000000
        print("Account balance: {} microAlgos, {} USDC\n".format(account_info.get('amount') / 1000000, assets))
    except:
        print("Account balance: {} microAlgos\n".format(account_info.get('amount') / 1000000))

    return algod_client


def teal_debug(client, group_txn):
    drr = transaction.create_dryrun(client, group_txn)

    filename = "dryrun.msgp"
    with open(filename, "wb") as f:
        f.write(base64.b64decode(encoding.msgpack_encode(drr)))


def print_creator_details():
    pvt_key, address = generate_creator_algorand_keypair()
    algod_client = get_algod_client(address)
    print("\n************CREATOR LOCAL STATE************")
    read_local_state(algod_client, address, APP_ID)


def print_stats():
    print("\n************APP DETAILS************")
    indexer_client = get_indexer_client()
    _, address = generate_notiboy_algorand_keypair()
    algod_client = get_algod_client(address)
    tot_users = 0
    tot_creators = 0
    tot_pub_msgs = 0
    tot_pvt_msgs = 0
    next_token = ""
    accts = []
    while True:
        data = indexer_client.accounts(application_id=APP_ID, limit=10, exclude='all', next_page=next_token)
        next_token = data['next-token']
        if len(data['accounts']) == 0:
            break

        for acct in data['accounts']:
            accts.append(acct['address'])
        time.sleep(300)

    for acct_addr in accts:
        acct = algod_client.account_info(acct_addr)
        acct_addr = acct['address']
        print("LOG: processing account dress", acct_addr)
        lstates = acct['apps-local-state']
        creator_found = False
        for lstate in lstates:
            if lstate['id'] != APP_ID:
                continue
            print("LOG: processing local state", lstate['key-value'])
            for kv in lstate['key-value']:
                if base64.b64decode(kv['key']).decode('utf-8') == 'whoami':
                    creator_found = True
                    break
            if creator_found:
                print("LOG: creator found")
                tot_creators += 1
                for kv in lstate['key-value']:
                    if base64.b64decode(kv['key']).decode('utf-8') == 'msgcount':
                        byte_value = base64.b64decode(kv['value'])
                        tot_pvt_msgs += int.from_bytes(byte_value[:8], "big")
                        tot_pub_msgs += int.from_bytes(byte_value[9:], "big")
                        break
            else:
                print("LOG: user found")
                tot_users += 1
            break

    print("Total Creators: {}, Total Users: {}".format(tot_creators, tot_users))
    print("Total Public Msgs: {}, Total Pvt Msgs: {}".format(tot_pub_msgs, tot_pvt_msgs))


def print_app_details():
    print("\n************APP DETAILS************")
    pvt_key, address = generate_notiboy_algorand_keypair()
    algod_client = get_algod_client(address)
    app_addr = logic.get_application_address(APP_ID)
    acct_info = algod_client.account_info(app_addr)
    app_acct_bal = acct_info['amount'] / 1000000
    app_acct_min_bal = acct_info['min-balance'] / 1000000
    print("App ID: {}, App Address: {}".format(APP_ID, app_addr))
    print("Balance: {} algos, Min Balance: {} algos".format(app_acct_bal, app_acct_min_bal))


def print_notiboy_details():
    pvt_key, address = generate_notiboy_algorand_keypair()
    algod_client = get_algod_client(address)
    print("\n************NOTIBOY BOX************")
    print_main_box(algod_client, APP_ID, "notiboy".encode('utf-8'))
    print("\n************NOTIBOY GLOBAL STATE************")
    print(read_global_state(algod_client, APP_ID))


def print_user_details():
    pvt_key, address = generate_user_algorand_keypair()
    algod_client = get_algod_client(address)
    # 32B public key of user
    box_name = encoding.decode_address(address)
    print("\n************USER LOCAL STATE************")
    read_local_state(algod_client, address, APP_ID)
    print("\n************USER BOX************")
    read_user_box(algod_client, APP_ID, box_name)


def print_account_local_state(address):
    algod_client = get_algod_client(address)
    read_local_state(algod_client, address, APP_ID)
