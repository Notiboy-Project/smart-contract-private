from creator_optin import creator_optin, creator_optout
from message import send_personal_notification, send_public_notification
from user_optin import user_optin, user_optout
from verify_dapp import verify_channel, unverify_channel


def optin():
    creator_optin()
    verify_channel()
    user_optin()


def msg():
    send_public_notification()
    send_personal_notification()


def optout():
    user_optout()
    unverify_channel()
    creator_optout()


def main():
    optin()
    msg()
    optout()


if __name__ == '__main__':
    main()
