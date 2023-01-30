from algosdk import account
from algosdk.future import transaction
from algosdk.v2client import algod

from client.lib.util import generate_creator_algorand_keypair, generate_notiboy_algorand_keypair, get_algod_client, \
    read_global_state_key, print_logs, generate_noop_txns, get_signed_grp_txn, print_main_box, get_val_main_box, debug
from client.lib.constants import *


# call application
def call_app(client, private_key, index, box_name, app_args, account_args, foreign_apps, num_noops):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("Verify from account: ", sender)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    boxes = [
        [0, box_name],
        [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""]
    ]

    # create unsigned transaction
    txn1 = transaction.ApplicationNoOpTxn(sender, params, index, app_args, foreign_apps=foreign_apps,
                                          accounts=account_args)
    noop_txns = generate_noop_txns(num_noops, sender, params, index, boxes=boxes, foreign_apps=[])

    signed_group = get_signed_grp_txn(txn1,
                                      *noop_txns,
                                      private_key=private_key)

    # send transaction
    tx_id = client.send_transactions(signed_group)

    # await confirmation
    transaction.wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print(
        "OptOut to app-id: {} in round: {}, txn: {}".format(index, transaction_response.get("confirmed-round"), tx_id))
    transaction_response = client.pending_transaction_info(signed_group[0].get_txid())
    print_logs(transaction_response)


def call_verify(value):
    pvt_key, address = generate_notiboy_algorand_keypair()
    _, creator_address = generate_creator_algorand_keypair()
    algod_client = get_algod_client(address)
    num_noops = 4
    dapp_name = DAPP_NAME
    # dapp_name = "Niftgen"
    app_args = [
        str.encode(value),
        str.encode(dapp_name),
    ]

    val = get_val_main_box(algod_client, APP_ID, "notiboy".encode('utf-8'), dapp_name)
    idx = val[0]
    entry = val[1]

    app_id = entry.split(":")[1]
    creator_address = algod_client.application_info(app_id)['params']['creator']
    foreign_apps = [
        int(app_id)
    ]
    acct_args = [
        creator_address
    ]

    app_args.append(
        # passing index to preventing for loop in SC in order to set verify bit in main box slot
        idx.to_bytes(8, 'big')
    )

    try:
        call_app(algod_client, pvt_key, APP_ID, MAIN_BOX, app_args, acct_args, foreign_apps, num_noops)
    except Exception as err:
        print("app call failed", err)

    print_main_box(algod_client, APP_ID, "notiboy".encode('utf-8'))


def verify_channel():
    print("\n*************CREATOR VERIFY START*************")
    call_verify("verify")
    print("*************CREATOR VERIFY END*************")


def unverify_channel():
    print("\n*************CREATOR UNVERIFY START*************")
    call_verify("unverify")
    print("*************CREATOR UNVERIFY END*************")
