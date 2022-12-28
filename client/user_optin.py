import base64

from algosdk import encoding
from client.lib.util import read_local_state, read_global_state, DAPP_NAME, APP_ID, generate_user_algorand_keypair, \
    get_algod_client, \
    debug, read_box, read_user_box
from client.message import send_personal_notification
from client.lib.opt import opt_in, opt_out
from client.lib.constants import *


def user_optin_out():
    pvt_key, address = generate_user_algorand_keypair(overwrite=False, fname="user-secret.txt", sandbox=True)
    algod_client = get_algod_client(pvt_key, address)
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
            print("LOCAL State:", read_local_state(algod_client, address, APP_ID))
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
            print("LOCAL State:", read_local_state(algod_client, address, APP_ID))
        except Exception as err:
            print("error opting out, err: {}".format(err))
        read_user_box(algod_client, APP_ID, box_name)

    print("Global state:", read_global_state(algod_client, APP_ID))


def user_optin():
    print("\n*************USER OPT-IN START*************")
    pvt_key, address = generate_user_algorand_keypair(overwrite=False, fname="user-secret.txt", sandbox=True)
    algod_client = get_algod_client(pvt_key, address)
    # 32B public key of user
    box_name = encoding.decode_address(address)

    num_noops = 1
    app_args = [
        str.encode("user")
    ]

    foreign_apps = []
    acct_args = []
    try:
        opt_in(algod_client, pvt_key, APP_ID, box_name, app_args, acct_args, foreign_apps, num_noops)
        print("LOCAL State:", read_local_state(algod_client, address, APP_ID))
    except Exception as err:
        print("error opting in, err: {}".format(err))
    read_user_box(algod_client, APP_ID, box_name)
    print("*************USER OPT-IN DONE*************")


def user_optout():
    print("\n*************USER OPT-OUT START*************")
    pvt_key, address = generate_user_algorand_keypair(overwrite=False, fname="user-secret.txt", sandbox=True)
    algod_client = get_algod_client(pvt_key, address)
    # 32B public key of user
    box_name = encoding.decode_address(address)

    num_noops = 1
    app_args = [
        str.encode("user")
    ]

    foreign_apps = []
    acct_args = []

    try:
        opt_out(algod_client, pvt_key, APP_ID, box_name, app_args, acct_args, foreign_apps, num_noops)
        print("LOCAL State:", read_local_state(algod_client, address, APP_ID))
    except Exception as err:
        print("error opting out, err: {}".format(err))

    print("Global state:", read_global_state(algod_client, APP_ID))
    print("*************USER OPT-OUT DONE*************")
