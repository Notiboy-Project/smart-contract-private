import ipdb

from datetime import datetime
from zoneinfo import ZoneInfo

from algosdk import account
from algosdk.future import transaction
from algosdk.v2client import algod
from algosdk.encoding import decode_address

from util import read_local_state, read_global_state, DAPP_NAME, APP_ID

SC_CREATOR_KEY = "9DyHfbCbo/ZZ+bG8/VGOlyikLm0bhf5u0/tpik6u74ugEC3cEXrSvwa+s8eHxzZFKrCVECPurvA/VxRbcuUjsg=="
SC_CREATOR_ADDR = "UAIC3XARPLJL6BV6WPDYPRZWIUVLBFIQEPXK54B7K4KFW4XFEOZNSSUKZI"


def get_algod_client(private_key, my_address):
    algod_address = "http://localhost:4001"
    algod_address = "https://node.testnet.algoexplorerapi.io"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(algod_token, algod_address)
    account_info = algod_client.account_info(my_address)
    print("Account balance: {} microAlgos\n".format(account_info.get('amount')))

    return algod_client


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

    return private_key, address


# call application
def call_app(client, private_key, index, app_args, acct_args):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("Call from account:", sender)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    print("app args {}, acct args {}".format(app_args, acct_args))
    # create unsigned transaction
    txn = transaction.ApplicationNoOpTxn(sender, params, index, app_args, acct_args)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    transaction.wait_for_confirmation(client, tx_id)
    print("Transaction ID:", tx_id)


def main():
    _, dapp_address = generate_algorand_keypair(False, "sndr-secret.txt")
    app_args = [
        str.encode("verify"),
        str.encode(DAPP_NAME)
    ]
    acct_args = [
        dapp_address
    ]
    algod_client = get_algod_client(SC_CREATOR_KEY, SC_CREATOR_ADDR)
    try:
        call_app(algod_client, SC_CREATOR_KEY, APP_ID, app_args, acct_args)
    except Exception as err:
        print("app call failed", err)

    print("Global state:", read_global_state(algod_client, APP_ID))


main()
