import base64

from algosdk import encoding
from client.lib.util import read_local_state, read_global_state, DAPP_NAME, APP_ID, generate_user_algorand_keypair, \
    get_algod_client, \
    debug, read_box
from client.lib.opt import opt_in, opt_out


def main():
    pvt_key, address = generate_user_algorand_keypair(overwrite=False, fname="user-secret.txt", sandbox=True)
    algod_client = get_algod_client(pvt_key, address)
    # 32B public key of user
    box_name = encoding.decode_address(address)

    for idx in range(1):
        idx += 1
        num_noops = 3
        app_args = [
            str.encode("user")
        ]

        foreign_apps = []
        acct_args = []
        try:
            print("\n*************OPT-IN*************")
            opt_in(algod_client, pvt_key, APP_ID, box_name, app_args, acct_args, foreign_apps, num_noops)
            read_box(algod_client, APP_ID, "notiboy")
        except Exception as err:
            print("error opting in, err: {}".format(err))

        try:
            print("\n*************OPT-OUT*************")
            opt_out(algod_client, pvt_key, APP_ID, box_name, app_args, acct_args, foreign_apps, num_noops)
            read_box(algod_client, APP_ID, "notiboy")
        except Exception as err:
            print("error opting out, err: {}".format(err))

    print("Global state:", read_global_state(algod_client, APP_ID))


if __name__ == '__main__':
    main()
