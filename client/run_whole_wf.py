from creator_optin import creator_optin, creator_optout, create_creator_app
from message import send_personal_notification, send_public_notification
from user_optin import user_optin, user_optout, user_opt_in_to_creator_app, user_opt_out_from_creator_app
from verify_dapp import verify_channel, unverify_channel
from admin import rename_channel
from lib.util import generate_notiboy_algorand_keypair, generate_user_algorand_keypair, \
    generate_creator_algorand_keypair, get_algod_client, print_creator_details, print_user_details, \
    print_notiboy_details, print_app_details, print_stats, print_account_local_state
from lib.constants import *
from launch_sc import launch_app


def print_data():
    print_creator_details()
    print_user_details()
    print_notiboy_details()
    print_app_details()
    print_stats()


def optin():
    creator_optin()
    # user_optin()
    # user_opt_in_to_creator_app()


def msg():
    send_public_notification()
    send_personal_notification()


def optout():
    user_opt_out_from_creator_app()
    user_optout()
    creator_optout()


def generate_accounts():
    overwrite = False
    _, addr = generate_notiboy_algorand_keypair(overwrite)
    get_algod_client(addr)
    _, addr = generate_user_algorand_keypair(overwrite)
    get_algod_client(addr)
    _, addr = generate_creator_algorand_keypair(overwrite)
    get_algod_client(addr)


def bootstrap():
    # Fund ALL accounts
    # Change notiboy address in SC and constants.py - NOTIBOY_ADDR
    generate_accounts()
    # Update constants.py - CREATOR_APP_ID
    create_creator_app()


def main():
    # Update constants.py - APP_ID
    # launch_app(update=True, bootstrap=False, reset=False)
    # bootstrap()
    # optin()
    # rename_channel()
    verify_channel("Algogator")
    # msg()
    # unverify_channel(DAPP_NAME)
    # optout()
    # print_data()
    # print_account_local_state("WWYET3KALUPE6O3XW67ET6WAMTLHPJMTC7AGJRJCIRGFVOLSGFFBUDHZMI")


if __name__ == '__main__':
    main()
