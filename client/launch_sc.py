from algosdk.future import transaction
from algosdk.v2client import algod
from algosdk.dryrun_results import DryrunResponse, StackPrinterConfig
from algosdk import account, logic

import base64

from sc.main_sc import approval_program, clear_state_program
from client.lib.util import read_global_state, print_main_box, generate_notiboy_algorand_keypair, get_algod_client, \
    compile_program
from client.lib.constants import *

DEBUG = False


def dev_test(client, private_key, app_id):
    # define sender as creator
    sender = account.address_from_private_key(private_key)
    print("resetting app by sender", sender)

    # get node suggested parameters
    params = client.suggested_params()

    app_args = [
        str.encode("test"),
    ]

    boxes = [
        [0, MAIN_BOX],
        [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""]
    ]

    # create unsigned transactions
    txn1 = transaction.ApplicationNoOpTxn(sender, params, app_id, note="txn1", app_args=app_args, boxes=boxes)
    txn2 = transaction.ApplicationNoOpTxn(sender, params, app_id, note="txn2", boxes=boxes)
    txn3 = transaction.ApplicationNoOpTxn(sender, params, app_id, note="txn3", boxes=boxes)
    txn4 = transaction.ApplicationNoOpTxn(sender, params, app_id, note="txn4", boxes=boxes)

    gid = transaction.calculate_group_id([txn1, txn2, txn3, txn4])
    transaction.assign_group_id([txn1, txn2, txn3, txn4], sender)
    txn1.gid = gid
    txn2.gid = gid
    txn3.gid = gid
    txn4.gid = gid

    # sign transaction
    signed_txn1 = txn1.sign(private_key)
    signed_txn2 = txn2.sign(private_key)
    signed_txn3 = txn3.sign(private_key)
    signed_txn4 = txn4.sign(private_key)
    signed_group = [signed_txn1, signed_txn2, signed_txn3, signed_txn4]

    # send transaction
    # debug()()
    tx_id = client.send_transactions(signed_group)

    # wait for confirmation
    try:
        transaction_response = transaction.wait_for_confirmation(client, tx_id)
        # print("TXID: ", tx_id)
        # print("Result confirmed in round: {}".format(transaction_response['confirmed-round']))

    except Exception as err:
        print(err)
        return

    print("Transaction ID:", tx_id)
    return app_id


# add main box
def bootstrap_app(client, private_key, app_id):
    # define sender as creator
    sender = account.address_from_private_key(private_key)
    print("bootstrapping app by sender", sender)

    # get node suggested parameters
    params = client.suggested_params()

    app_args = [
        str.encode("bootstrap"),
    ]

    boxes = [
        [0, MAIN_BOX],
        [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""]
    ]

    # create unsigned transactions
    txn1 = transaction.ApplicationNoOpTxn(sender, params, app_id, note="txn1", app_args=app_args, boxes=boxes)
    txn2 = transaction.ApplicationNoOpTxn(sender, params, app_id, note="txn2", boxes=boxes)
    txn3 = transaction.ApplicationNoOpTxn(sender, params, app_id, note="txn3", boxes=boxes)
    txn4 = transaction.ApplicationNoOpTxn(sender, params, app_id, note="txn4", boxes=boxes)

    gid = transaction.calculate_group_id([txn1, txn2, txn3, txn4])
    transaction.assign_group_id([txn1, txn2, txn3, txn4], sender)
    txn1.gid = gid
    txn2.gid = gid
    txn3.gid = gid
    txn4.gid = gid

    # sign transaction
    signed_txn1 = txn1.sign(private_key)
    signed_txn2 = txn2.sign(private_key)
    signed_txn3 = txn3.sign(private_key)
    signed_txn4 = txn4.sign(private_key)
    signed_group = [signed_txn1, signed_txn2, signed_txn3, signed_txn4]

    # send transaction
    # debug()()
    tx_id = client.send_transactions(signed_group)

    # wait for confirmation
    try:
        transaction_response = transaction.wait_for_confirmation(client, tx_id)
        # print("TXID: ", tx_id)
        # print("Result confirmed in round: {}".format(transaction_response['confirmed-round']))

    except Exception as err:
        print(err)
        return

    print("Transaction ID:", tx_id)
    return app_id


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
                                           local_schema, extra_pages=2)

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
    app_addr = logic.get_application_address(APP_ID)
    print("Application address:", app_addr)

    return app_id


# create new application
def update_app(client, private_key, approval_program, clear_program, app_id):
    # define sender as creator
    sender = account.address_from_private_key(private_key)

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


def launch_app(update, bootstrap, reset):
    pvt_key, address = generate_notiboy_algorand_keypair()
    algod_client = get_algod_client(address)

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
    print("Deploying Countermnemonic application......")

    # create new application
    if not update:
        # FUND SC acct after creation for bootstrap to work
        # ./sandbox goal app info --app-id 1
        app_id = create_app(algod_client, pvt_key, approval_program_compiled, clear_state_program_compiled,
                            global_schema, local_schema)
        return
    else:
        app_id = APP_ID

    if update:
        update_app(algod_client, pvt_key, approval_program_compiled, clear_state_program_compiled, app_id)
    if reset:
        dev_test(algod_client, pvt_key, app_id)
    if bootstrap:
        bootstrap_app(algod_client, pvt_key, app_id)

    print(read_global_state(algod_client, app_id))
    print_main_box(algod_client, app_id, "notiboy".encode('utf-8'))
