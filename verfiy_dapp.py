import ipdb

from datetime import datetime
from zoneinfo import ZoneInfo

from algosdk import account
from algosdk.future import transaction
from algosdk.v2client import algod
from algosdk.encoding import decode_address

from call_sc import generate_algorand_keypair, get_algod_client
from util import read_local_state, read_global_state, DAPP_NAME, APP_ID

SC_CREATOR_KEY = "9DyHfbCbo/ZZ+bG8/VGOlyikLm0bhf5u0/tpik6u74ugEC3cEXrSvwa+s8eHxzZFKrCVECPurvA/VxRbcuUjsg=="
SC_CREATOR_ADDR = "UAIC3XARPLJL6BV6WPDYPRZWIUVLBFIQEPXK54B7K4KFW4XFEOZNSSUKZI"


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

    # create unsigned transaction
    txn = transaction.ApplicationNoOpTxn(sender, params, index, app_args, acct_args)

    # sign transaction
    signed_txn1 = txn.sign(private_key)

    # send transaction
    tx_id = client.send_transactions([signed_txn1])

    # await confirmation
    transaction.wait_for_confirmation(client, tx_id)
    print("Transaction ID:", tx_id)


def main():
    _, dapp_address = generate_algorand_keypair(False, "sndr-secret.txt")
    app_args = [
        str.encode("verify"),
        str.encode(DAPP_NAME),
    ]
    acct_args = [
        dapp_address
    ]
    algod_client = get_algod_client(SC_CREATOR_KEY, SC_CREATOR_ADDR)
    call_app(algod_client, SC_CREATOR_KEY, APP_ID, app_args, acct_args)


main()
