from client.lib.util import read_local_state, read_global_state, DAPP_NAME, APP_ID, generate_creator_algorand_keypair, \
    get_algod_client, read_global_state_key, \
    MAIN_BOX, read_box
from client.lib.opt import opt_in, opt_out
from client.lib.constants import *
from client.message import send_public_notification


def main():
    pvt_key, address = generate_creator_algorand_keypair(overwrite=False, fname="creator-secret.txt", sandbox=True)
    algod_client = get_algod_client(pvt_key, address)

    # create test.teal with following
    # #pragma version 7
    # int 1
    # ./sandbox copyTo test.teal
    # WARN: should be strictly 64 global byteslices and 16 local byteslices
    # ./sandbox goal app create --creator EVYC4CFP533BRC26OLGJEWJJ4SDB5JZJPNFPOZ7R56QUENTTUDQDLNJGTM --global-byteslices 64 --global-ints 0 --local-byteslices 16 --local-ints 0 --approval-prog test.teal  --clear-prog test.teal
    # Pass created app id as arg
    for idx in range(1):
        idx += 1
        num_noops = 4
        dapp_name = 'dapp' + str(idx)
        app_args = [
            str.encode("dapp"),
            str.encode(dapp_name),
        ]

        foreign_apps = [
            CREATOR_APP_ID
        ]
        acct_args = []
        try:
            print("\n*************OPT-IN*************")
            opt_in(algod_client, pvt_key, APP_ID, MAIN_BOX, app_args, acct_args, foreign_apps, num_noops)
        except Exception as err:
            print("error opting in, err: {}".format(err))
        read_box(algod_client, APP_ID, "notiboy")

        # public message
        print("\n*************PUBLIC MSG*************")
        send_public_notification()

        # OPT OUT
        nxt_idx = read_global_state_key(algod_client, APP_ID, "index")
        app_args.append(
            # passing index to preventing for loop in SC in order to clear outmain box slot
            (nxt_idx).to_bytes(8, 'big')
        )
        try:
            print("\n*************OPT-OUT*************")
            opt_out(algod_client, pvt_key, APP_ID, MAIN_BOX, app_args, acct_args, foreign_apps, num_noops)
        except Exception as err:
            print("error opting out, err: {}".format(err))
        read_box(algod_client, APP_ID, "notiboy")

    print("Global state:", read_global_state(algod_client, APP_ID))


if __name__ == '__main__':
    main()
