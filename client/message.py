from collections import OrderedDict
from algosdk import account
from algosdk.future import transaction

from client.lib.util import read_local_state, debug, generate_creator_algorand_keypair, \
    get_algod_client, generate_noop_txns, \
    get_signed_grp_txn
from client.lib.constants import *


def send(client, private_key, index, msg, app_args, foreign_apps, acct_args, num_noops, box_name):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("Call from account:", sender)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000
    boxes = [
        [0, box_name],
        [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""]
        , [0, ""]
    ]

    # create unsigned transaction
    txn1 = transaction.ApplicationNoOpTxn(sender, params, index, app_args, acct_args, foreign_apps=foreign_apps,
                                          note=str.encode(msg))

    noop_txns = []
    if num_noops > 0:
        noop_txns = generate_noop_txns(num_noops, sender, params, index, boxes=boxes, foreign_apps=[])

    # sign transaction
    signed_group = get_signed_grp_txn(txn1, *noop_txns, private_key=private_key)

    # send transaction
    tx_id = client.send_transactions(signed_group)

    # await confirmation
    transaction.wait_for_confirmation(client, tx_id)
    print("Transaction ID:", tx_id)


def send_public_notification():
    pvt_key, address = generate_creator_algorand_keypair(overwrite=False, fname="creator-secret.txt", sandbox=True)
    algod_client = get_algod_client(pvt_key, address)

    for idx in range(1):
        idx += 1
        app_args = [
            str.encode("pub_notify"),
        ]
        foreign_apps = [
            9
        ]

        msg = "Hi Sending notification {} adding very very long msg. This will be trimmed to 120 chars. You won't see remaining messagexxxxxxxxxxxxxxxxxx".format(
            idx)
        try:
            send(algod_client, pvt_key, APP_ID, msg, app_args, foreign_apps, [], 0, "")
        except Exception as err:
            print("error calling app, err: {}".format(err))

    print("LOCAL State:")
    read_local_state(algod_client, address, APP_ID)


def send_personal_notification():
    pvt_key, address = generate_creator_algorand_keypair(overwrite=False, fname="creator-secret.txt", sandbox=True)
    algod_client = get_algod_client(pvt_key, address)

    box_name = ""
    for idx in range(16):
        idx += 1
        num_noops = 4
        dapp_name = 'dapp' + str(idx)
        app_args = [
            str.encode("pvt_notify"),
            str.encode(dapp_name),
            str.encode("{}".format(CREATOR_APP_ID))
        ]

        foreign_apps = [
            CREATOR_APP_ID
        ]

        msg = "Hi, sending a very very very long personal notification numbered {}." \
              " This will be trimmed to 120 chars. You won't see remaining messagexxxxxxxxxxxxxxxxxx".format(
            idx)
        try:
            send(algod_client, pvt_key, APP_ID, msg, app_args, foreign_apps, [], num_noops, box_name)
        except Exception as err:
            print("error calling app, err: {}".format(err))

    print("LOCAL State:")
    read_local_state(algod_client, address, APP_ID)
