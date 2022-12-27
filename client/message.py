from algosdk import account
from algosdk.future import transaction
from algosdk import encoding

from client.lib.util import read_local_state, debug, generate_creator_algorand_keypair, \
    get_algod_client, generate_noop_txns, read_box, \
    get_signed_grp_txn, read_global_state_key, read_user_box, print_logs
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
    transaction_response = client.pending_transaction_info(signed_group[0].get_txid())
    print_logs(transaction_response)


def send_public_notification():
    print("\n*************PUBLIC MSG START*************")
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
    print("*************PUBLIC MSG END*************")


def send_personal_notification():
    print("\n*************PERSONAL NOTIFICATION START*************")
    pvt_key, address = generate_creator_algorand_keypair(overwrite=False, fname="creator-secret.txt", sandbox=True)
    algod_client = get_algod_client(pvt_key, address)

    RECEIVER = "AAVUPELO5ZCBDA3DD3G7ZDZ64BSEOOE3G7ZBOMR7DKI3YIBXLYEC3EATQA"
    box_name = encoding.decode_address(RECEIVER)
    for idx in range(1):
        idx += 1
        num_noops = 4
        dapp_name = 'dapp' + str(idx)
        app_args = [
            str.encode("pvt_notify"),
            str.encode(dapp_name),
        ]

        foreign_apps = [
            CREATOR_APP_ID
        ]

        acct_args = [
            RECEIVER
        ]

        nxt_idx = read_global_state_key(algod_client, APP_ID, "index")
        app_args.append(
            # passing index to preventing for loop in SC in order to verify if creator is present in box slot
            (nxt_idx).to_bytes(8, 'big')
        )
        msg = "Hi, sending a very very very long personal notification numbered {}." \
              " This will be trimmed to 1008 chars.".format(
            idx)
        try:
            # user has to opt in to creator's app before receiving message
            # ./sandbox goal app optin --app-id 9 -f AAVUPELO5ZCBDA3DD3G7ZDZ64BSEOOE3G7ZBOMR7DKI3YIBXLYEC3EATQA
            send(algod_client, pvt_key, APP_ID, msg, app_args, foreign_apps, acct_args, num_noops, box_name)
        except Exception as err:
            print("error calling app, err: {}".format(err))

    print("USER LOCAL State:")
    read_local_state(algod_client, RECEIVER, APP_ID)
    print("CREATOR LOCAL State:")
    read_local_state(algod_client, address, APP_ID)
    read_user_box(algod_client, APP_ID, box_name)
    print("*************PERSONAL NOTIFICATION END*************")
