from algosdk.future import transaction
from algosdk.v2client import algod
from pyteal import *
from algosdk import account, mnemonic, logic

import base64

from sc import approval_program, clear_state_program

APP_ID = 94241155

def generate_algorand_keypair():
    # private_key, address = account.generate_account()
    # print("My address: {}".format(address))
    # print("My private key: {}".format(private_key))
    # print("My passphrase: {}".format(mnemonic.from_private_key(private_key)))

    private_key = "9DyHfbCbo/ZZ+bG8/VGOlyikLm0bhf5u0/tpik6u74ugEC3cEXrSvwa+s8eHxzZFKrCVECPurvA/VxRbcuUjsg=="
    address = "UAIC3XARPLJL6BV6WPDYPRZWIUVLBFIQEPXK54B7K4KFW4XFEOZNSSUKZI"

    return private_key, address


def get_algod_client(private_key, my_address):
    algod_address = "http://localhost:4001"
    # algod_address = "https://node.testnet.algoexplorerapi.io"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(algod_token, algod_address)
    account_info = algod_client.account_info(my_address)
    print("Account balance: {} microAlgos\n".format(account_info.get('amount')))

    return algod_client


def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response['result'])


# create new application
def create_app(client, private_key, approval_program, clear_program, global_schema, local_schema):
    # define sender as creator
    sender = account.address_from_private_key(private_key)

    # declare on_complete as NoOp
    on_complete = transaction.OnComplete.NoOpOC.real

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.ApplicationCreateTxn(sender, params, on_complete, approval_program, clear_program, global_schema, local_schema)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # wait for confirmation
    try:
        transaction_response = transaction.wait_for_confirmation(client, tx_id, 4)
        print("TXID: ", tx_id)
        print("Result confirmed in round: {}".format(transaction_response['confirmed-round']))

    except Exception as err:
        print(err)
        return

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    app_id = transaction_response['application-index']
    print("Created new app-id:", app_id)

    return app_id


# create new application
def update_app(client, private_key, approval_program, clear_program, app_id):
    # define sender as creator
    sender = account.address_from_private_key(private_key)

    # declare on_complete as NoOp
    on_complete = transaction.OnComplete.NoOpOC.real

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.ApplicationUpdateTxn(sender, params, int(app_id), approval_program, clear_program)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # wait for confirmation
    try:
        transaction_response = transaction.wait_for_confirmation(client, tx_id, 4)
        print("TXID: ", tx_id)
        print("Result confirmed in round: {}".format(transaction_response['confirmed-round']))

    except Exception as err:
        print(err)
        return

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    app_id = transaction_response.get('txn').get('txn').get('apid')
    print("Updated app-id:", app_id)

    return app_id

# helper function that formats global state for printing
def format_state(state):
    formatted = {}
    for item in state:
        key = item['key']
        value = item['value']
        formatted_key = base64.b64decode(key).decode('utf-8')
        if value['type'] == 1:
            # byte string
            if formatted_key == 'voted':
                formatted_value = base64.b64decode(value['bytes']).decode('utf-8')
            else:
                formatted_value = value['bytes']
            formatted[formatted_key] = formatted_value
        else:
            # integer
            formatted[formatted_key] = value['uint']
    return formatted


# helper function to read app global state
def read_global_state(client, app_id):
    app = client.application_info(app_id)
    global_state = app['params']['global-state'] if "global-state" in app['params'] else []
    return format_state(global_state)


# read user local state
def read_local_state(client, addr, app_id):
    results = client.account_info(addr)
    for local_state in results["apps-local-state"]:
        if local_state["id"] == app_id:
            if "key-value" not in local_state:
                return {}
            return format_state(local_state["key-value"])
    return {}


def main():
    pvt_key, address = generate_algorand_keypair()
    algod_client = get_algod_client(pvt_key, address)

    # declare application state storage (immutable)
    # 16 local kv pairs, each pair 128 bytes
    local_ints = 0
    local_bytes = 16
    local_schema = transaction.StateSchema(local_ints, local_bytes)
    # 64 global kv pairs, each pair 128 bytes
    global_ints = 0
    global_bytes = 64
    global_schema = transaction.StateSchema(global_ints, global_bytes)


    # compile program to TEAL assembly
    with open("./approval.teal", "w") as f:
        approval_program_teal = approval_program()
        f.write(approval_program_teal)

    # compile program to TEAL assembly
    with open("./clear.teal", "w") as f:
        clear_state_program_teal = clear_state_program()
        f.write(clear_state_program_teal)

    # compile program to binary
    approval_program_compiled = compile_program(algod_client, approval_program_teal)

    # compile program to binary
    clear_state_program_compiled = compile_program(algod_client, clear_state_program_teal)

    print("--------------------------------------------")
    print("Deploying Counter application......")

    # create new application
    # app_id = create_app(algod_client, pvt_key, approval_program_compiled, clear_state_program_compiled,
    #                     global_schema, local_schema)

    app_id = APP_ID
    # update_app(algod_client, pvt_key, approval_program_compiled, clear_state_program_compiled, app_id)

    # read global state of application
    print("Global state:", read_global_state(algod_client, app_id))

    print("Local state:", read_local_state(algod_client, "JAWNLEFIR7ID4XM27FJ4GU57CN4HAZLGETWO2N7KHREN3G64DCQ37HJ5UU", APP_ID))


main()
