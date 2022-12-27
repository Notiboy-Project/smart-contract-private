from creator_optin import creator_optin, creator_optout
from message import send_personal_notification, send_public_notification
from user_optin import user_optin, user_optout


def run():
    creator_optin()
    user_optin()
    send_public_notification()
    send_personal_notification()


def clean():
    user_optout()
    creator_optout()


def main():
    run()
    clean()


if __name__ == '__main__':
    main()
