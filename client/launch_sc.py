from algosdk.future import transaction
from algosdk.v2client import algod
from algosdk.dryrun_results import DryrunResponse, StackPrinterConfig
from algosdk import account, mnemonic

import base64

from creator_sc import approval_program, clear_state_program
from util import read_global_state, APP_ID

DEBUG = False


# ./sandbox/sandbox goal account list
# ./sandbox/sandbox goal account export -a ZIC23NIY7IJVIQ5NEWXV5B7TIHNV4ZEHGT2IHYEMJSDEYV75DB4DNO67CY
def generate_algorand_keypair():
    # private_key, address = account.generate_account()
    # print("My address: {}".format(address))
    # print("My private key: {}".format(private_key))
    # print("My passphrase: {}".format(mnemonic.from_private_key(private_key)))

    private_key = "Fa6ctT9AZhWWtnL5/ASqqy4HNq8kCz1UWwbHGRAiGGL16CyzvQTyGfwoT9HwWRr7bJFbwUAfYpjdXjg3cBueYQ=="
    mnemonic_string = "simple vocal hard wall gravity tide surface eight pull oil fruit basic word assist answer still bright prevent coil speak loan clean wild able minimum"
    if mnemonic_string != "":
        private_key = mnemonic.to_private_key(mnemonic_string)
    address = "ZIC23NIY7IJVIQ5NEWXV5B7TIHNV4ZEHGT2IHYEMJSDEYV75DB4DNO67CY"

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
    txn = transaction.ApplicationCreateTxn(sender, params, on_complete, approval_program, clear_program, global_schema,
                                           local_schema, extra_pages=1)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # debug
    if DEBUG:
        drr = transaction.create_dryrun(client, [signed_txn])
        dryrun_result = DryrunResponse(client.dryrun(drr))
        for txn in dryrun_result.txns:
            if txn.app_call_rejected():
                print(txn.app_trace(StackPrinterConfig(max_value_width=0)))

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
    update_app(algod_client, pvt_key, approval_program_compiled, clear_state_program_compiled, app_id)

    print("Global state:", read_global_state(algod_client, app_id))


main()
