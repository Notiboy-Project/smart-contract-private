from datetime import datetime
from zoneinfo import ZoneInfo

from algosdk import account, mnemonic, logic
from algosdk import account, logic
from algosdk import encoding
import base64
from algosdk.future import transaction
from algosdk.v2client import algod
from algosdk.encoding import decode_address

from client.lib.util import read_local_state, read_global_state, DAPP_NAME, APP_ID, \
    get_algod_client, \
    NOTIBOY_ADDR, teal_debug, debug, \
    generate_noop_txns, get_signed_grp_txn, print_logs
from client.lib.constants import *


def opt_out(client, private_key, index, box_name, app_args, account_args, foreign_apps, num_noops):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("OptOut from account: ", sender)

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
    if len(foreign_apps) != 0:
        txn1 = transaction.ApplicationCloseOutTxn(sender, params, index, app_args, foreign_apps=foreign_apps)
    else:
        txn1 = transaction.ApplicationCloseOutTxn(sender, params, index, app_args, boxes=boxes)
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
    print_logs(transaction_response)


def opt_in(client, private_key, index, box_name, app_args, account_args, foreign_apps, num_noops):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("OptIn from account: ", sender)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    # params.flat_fee = True
    # params.fee = 1000

    boxes = [
        [0, box_name],
        [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""]
        , [0, ""]
    ]

    # create unsigned transactions

    # creator flow
    if len(foreign_apps) != 0:
        if RUNNING_MODE == SANDBOX:
            # pay 1 algo
            txn1 = transaction.PaymentTxn(sender, params, NOTIBOY_ADDR, 1000000)
            txn2 = transaction.ApplicationOptInTxn(sender, params, index, app_args, foreign_apps=foreign_apps)
        elif RUNNING_MODE in [TESTNET, MAINNET]:
            # pay 25 USDC
            txn1 = transaction.AssetTransferTxn(sender, params, NOTIBOY_ADDR, 25000000, ASA_ASSET)
            txn2 = transaction.ApplicationOptInTxn(sender, params, index, app_args, foreign_assets=[ASA_ASSET],
                                                   foreign_apps=foreign_apps)
    else:
        # user flow
        if RUNNING_MODE == SANDBOX:
            # pay 1 algo
            txn1 = transaction.PaymentTxn(sender, params, logic.get_application_address(APP_ID), 1000000)
        elif RUNNING_MODE in [TESTNET, MAINNET]:
            # pay 5 algo
            txn1 = transaction.PaymentTxn(sender, params, logic.get_application_address(APP_ID), 5000000)
        txn2 = transaction.ApplicationOptInTxn(sender, params, index, app_args, boxes=boxes)
    noop_txns = generate_noop_txns(num_noops, sender, params, index, boxes=boxes, foreign_apps=[])

    signed_group = get_signed_grp_txn(txn1, txn2,
                                      *noop_txns,
                                      private_key=private_key)

    # teal_debug(client, signed_group)
    # return
    # send transaction
    tx_id = client.send_transactions(signed_group)

    # await confirmation
    transaction.wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("OptIn to app-id: {} in round: {}, txn: {}".format(index, transaction_response.get("confirmed-round"), tx_id))

    transaction_response = client.pending_transaction_info(signed_group[1].get_txid())
    print_logs(transaction_response)
