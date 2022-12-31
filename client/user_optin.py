import base64
from algosdk import account
from algosdk import encoding
from client.lib.util import read_local_state, read_global_state, get_signed_grp_txn, APP_ID, \
    generate_user_algorand_keypair, \
    get_algod_client, \
    debug, read_box, read_user_box
from algosdk.future import transaction

from client.message import send_personal_notification
from client.lib.opt import opt_in, opt_out
from client.lib.constants import *


def user_opt_in_to_creator_app():
    print("\n*************USER OPT-IN TO CREATOR START*************")
    app_id = CREATOR_APP_ID
    # declare sender
    private_key, sender = generate_user_algorand_keypair(fname="user-secret.txt")
    client = get_algod_client(sender)
    print("OptIn from account: ", sender)

    # get node suggested parameters
    params = client.suggested_params()

    txn = transaction.ApplicationOptInTxn(sender, params, app_id)
    signed_group = get_signed_grp_txn(txn, private_key=private_key)

    # send transaction
    tx_id = client.send_transactions(signed_group)

    # await confirmation
    transaction.wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("User OptIn to app-id: {} in round: {}, txn: {}".format(app_id, transaction_response.get("confirmed-round"),
                                                                  tx_id))
    print("*************USER OPT-IN TO CREATOR END*************")


def user_opt_out_from_creator_app():
    print("\n*************USER OPT-OUT FROM CREATOR START*************")
    app_id = CREATOR_APP_ID
    # declare sender
    private_key, sender = generate_user_algorand_keypair(fname="user-secret.txt")
    client = get_algod_client(sender)
    print("OptIn from account: ", sender)

    # get node suggested parameters
    params = client.suggested_params()

    txn = transaction.ApplicationClearStateTxn(sender, params, app_id)
    signed_group = get_signed_grp_txn(txn, private_key=private_key)

    # send transaction
    tx_id = client.send_transactions(signed_group)

    # await confirmation
    transaction.wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("User OptIn to app-id: {} in round: {}, txn: {}".format(app_id, transaction_response.get("confirmed-round"),
                                                                  tx_id))
    print("*************USER OPT-OUT FROM CREATOR END*************")


def user_optin_out():
    pvt_key, address = generate_user_algorand_keypair(fname="user-secret.txt")
    algod_client = get_algod_client(address)
    # 32B public key of user
    box_name = encoding.decode_address(address)

    for idx in range(1):
        idx += 1
        num_noops = 1
        app_args = [
            str.encode("user")
        ]

        foreign_apps = []
        acct_args = []
        try:
            print("\n*************USER OPT-IN START*************")
            opt_in(algod_client, pvt_key, APP_ID, box_name, app_args, acct_args, foreign_apps, num_noops)
            print("*************USER OPT-IN DONE*************")
            read_local_state(algod_client, address, APP_ID)
        except Exception as err:
            print("error opting in, err: {}".format(err))
        read_user_box(algod_client, APP_ID, box_name)

        print("\n*************PERSONAL NOTIFICATION START*************")
        send_personal_notification()
        print("*************PERSONAL NOTIFICATION DONE*************")
        read_user_box(algod_client, APP_ID, box_name)

        try:
            print("\n*************USER OPT-OUT START*************")
            opt_out(algod_client, pvt_key, APP_ID, box_name, app_args, acct_args, foreign_apps, num_noops)
            print("*************USER OPT-OUT DONE*************")
            read_local_state(algod_client, address, APP_ID)
        except Exception as err:
            print("error opting out, err: {}".format(err))
        read_user_box(algod_client, APP_ID, box_name)

    print("Global state:", read_global_state(algod_client, APP_ID))


def user_optin():
    print("\n*************USER OPT-IN START*************")
    pvt_key, address = generate_user_algorand_keypair(fname="user-secret.txt")
    algod_client = get_algod_client(address)
    # 32B public key of user
    box_name = encoding.decode_address(address)

    num_noops = 0
    app_args = [
        str.encode("user")
    ]

    foreign_apps = []
    acct_args = []
    try:
        opt_in(algod_client, pvt_key, APP_ID, box_name, app_args, acct_args, foreign_apps, num_noops)
        read_local_state(algod_client, address, APP_ID)
    except Exception as err:
        print("error opting in, err: {}".format(err))
    read_user_box(algod_client, APP_ID, box_name)
    print("*************USER OPT-IN DONE*************")


def user_optout():
    print("\n*************USER OPT-OUT START*************")
    pvt_key, address = generate_user_algorand_keypair(fname="user-secret.txt")
    algod_client = get_algod_client(address)
    # 32B public key of user
    box_name = encoding.decode_address(address)

    num_noops = 0
    app_args = [
        str.encode("user")
    ]

    foreign_apps = []
    acct_args = []

    try:
        opt_out(algod_client, pvt_key, APP_ID, box_name, app_args, acct_args, foreign_apps, num_noops)
        read_local_state(algod_client, address, APP_ID)
    except Exception as err:
        print("error opting out, err: {}".format(err))

    print("Global state:", read_global_state(algod_client, APP_ID))
    print("*************USER OPT-OUT DONE*************")
