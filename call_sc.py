import sys

import ipdb

from datetime import datetime
from zoneinfo import ZoneInfo

from algosdk import account
from algosdk.future import transaction
from algosdk.v2client import algod
from algosdk.encoding import decode_address

from util import read_local_state, read_global_state, DAPP_NAME, APP_ID


def opt_in(client, private_key, index, dapp_name):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("OptIn from account: ", sender)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    if dapp_name == "":
        app_args = [
            str.encode("user"),
        ]
    else:
        app_args = [
            str.encode("dapp"),
            str.encode(dapp_name),
        ]

    print("app_args: ", app_args)

    # create unsigned transaction
    txn2 = transaction.ApplicationOptInTxn(sender, params, index, app_args)

    # pay 1 algo
    txn1 = transaction.PaymentTxn(sender, params, "HZ57J3K46JIJXILONBBZOHX6BKPXEM2VVXNRFSUED6DKFD5ZD24PMJ3MVA",
                                  1000000)

    gid = transaction.calculate_group_id([txn1, txn2])
    transaction.assign_group_id([txn1, txn2])
    txn1.gid = gid
    txn2.gid = gid

    # sign transaction
    signed_txn1 = txn1.sign(private_key)
    signed_txn2 = txn2.sign(private_key)
    signed_group = [signed_txn1, signed_txn2]

    # send transaction
    tx_id = client.send_transactions(signed_group)

    # await confirmation
    transaction.wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("OptIn to app-id: {} in round: {}".format(index, transaction_response.get("confirmed-round")))


# call application
def call_app(client, private_key, index, msg, app_args, acct_args):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("Call from account:", sender)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    # create unsigned transaction
    txn2 = transaction.ApplicationNoOpTxn(sender, params, index, app_args, acct_args, note=str.encode(msg))

    # pay 0 algo
    txn1 = transaction.PaymentTxn(sender, params, "HZ57J3K46JIJXILONBBZOHX6BKPXEM2VVXNRFSUED6DKFD5ZD24PMJ3MVA",
                                  0)

    gid = transaction.calculate_group_id([txn1, txn2])
    transaction.assign_group_id([txn1, txn2])
    txn1.gid = gid
    txn2.gid = gid

    # sign transaction
    signed_txn1 = txn1.sign(private_key)
    signed_txn2 = txn2.sign(private_key)
    signed_group = [signed_txn1, signed_txn2]

    # send transaction
    tx_id = client.send_transactions(signed_group)

    # await confirmation
    transaction.wait_for_confirmation(client, tx_id)
    print("Transaction ID:", tx_id)


def generate_algorand_keypair(overwrite, fname):
    if overwrite:
        private_key, address = account.generate_account()
        with open(fname, "w") as f:
            f.write('{}\n{}\n'.format(address, private_key))
    else:
        with open(fname, "r") as f:
            lns = f.readlines()
            address = lns[0].rstrip('\n')
            private_key = lns[1].rstrip('\n')

    print("My address: {}".format(address))
    print("My private key: {}".format(private_key))

    if overwrite:
        sys.exit()

    return private_key, address


def get_algod_client(private_key, my_address):
    algod_address = "http://localhost:4001"
    algod_address = "https://node.testnet.algoexplorerapi.io"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(algod_token, algod_address)
    account_info = algod_client.account_info(my_address)
    print("Account balance: {} microAlgos\n".format(account_info.get('amount')))

    return algod_client


def pvt_notify():
    # gen_new_address = True
    gen_new_address = False
    pvt_key, rcvr_address = generate_algorand_keypair(gen_new_address, "rcvr-secret.txt")
    algod_client = get_algod_client(pvt_key, rcvr_address)

    try:
        pass
        # opt_in(algod_client, pvt_key, APP_ID, "")
    except Exception as err:
        print("error opting in, err: {}".format(err))

    msg = "This is my personal msg at" + datetime.now(ZoneInfo('Asia/Kolkata')).strftime("%m/%d/%Y, %H:%M:%S")
    print("Sending private notification --> {}".format(msg))

    try:
        # gen_new_address = True
        gen_new_address = False
        pvt_key, address = generate_algorand_keypair(gen_new_address, "sndr-secret.txt")
        algod_client = get_algod_client(pvt_key, address)

        app_args = [
            str.encode("pvt_notify"),
            str.encode(DAPP_NAME),
        ]
        acct_args = [
            rcvr_address
        ]
        call_app(algod_client, pvt_key, APP_ID, msg, app_args, acct_args)
    except Exception as err:
        print("error calling app, err: {}".format(err))

    print("Local state of receiver ", rcvr_address)
    local_state = read_local_state(algod_client, rcvr_address, APP_ID)

    for k, v in local_state.items():
        print("{} --> {}".format(k, v))


def main():
    # gen_new_address = True
    gen_new_address = False
    pvt_key, address = generate_algorand_keypair(gen_new_address, "sndr-secret.txt")
    algod_client = get_algod_client(pvt_key, address)

    try:
        pass
        # opt_in(algod_client, pvt_key, APP_ID, DAPP_NAME)
    except Exception as err:
        print("error opting in, err: {}".format(err))

    msg = "This is my public msg at" + datetime.now(ZoneInfo('Asia/Kolkata')).strftime("%m/%d/%Y, %H:%M:%S")
    print("Sending notification --> {}".format(msg))
    try:
        app_args = [
            str.encode("pub_notify"),
            str.encode(DAPP_NAME),
        ]
        # call_app(algod_client, pvt_key, APP_ID, msg, app_args, [])
    except Exception as err:
        print("error calling app, err: {}".format(err))

    print("Global state:", read_global_state(algod_client, APP_ID))

    print("Local state of sender")
    local_state = read_local_state(algod_client, address, APP_ID)

    for k, v in local_state.items():
        print("{} --> {}".format(k, v))

    pvt_notify()


main()
