from client.lib.util import read_local_state, read_global_state, DAPP_NAME, APP_ID, generate_creator_algorand_keypair, \
    get_algod_client, \
    MAIN_BOX
from client.lib.opt import opt_in, opt_out


def main():
    pvt_key, address = generate_creator_algorand_keypair(overwrite=False, fname="creator-secret.txt", sandbox=True)
    algod_client = get_algod_client(pvt_key, address)

    # create test.teal with following
    # #pragma version 7
    # int 1
    # ./sandbox copyTo test.teal
    # ./sandbox goal app create --creator EVYC4CFP533BRC26OLGJEWJJ4SDB5JZJPNFPOZ7R56QUENTTUDQDLNJGTM --global-byteslices 64 --global-ints 0 --local-byteslices 16 --local-ints 0 --approval-prog test.teal  --clear-prog test.teal
    # Pass created app id as arg
    app_args = [
        str.encode("dapp"),
        str.encode(DAPP_NAME),
        str.encode("10")
    ]

    foreign_apps = [
        10
    ]
    acct_args = []

    try:
        pass
        opt_in(algod_client, pvt_key, APP_ID, DAPP_NAME, MAIN_BOX, app_args, acct_args, foreign_apps)
    except Exception as err:
        print("error opting in, err: {}".format(err))

    try:
        pass
        opt_out(algod_client, pvt_key, APP_ID, DAPP_NAME)
    except Exception as err:
        print("error opting out, err: {}".format(err))


if __name__ == '__main__':
    main()
