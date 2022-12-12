from algosdk import account
from algosdk.v2client import algod

import base64
from algosdk.future.transaction import LogicSigAccount


def generate_algorand_keypair(overwrite):
    if overwrite:
        private_key, address = account.generate_account()
        with open("secret.txt", "w") as f:
            f.write('{}\n{}\n'.format(address, private_key))
    else:
        with open("secret.txt", "r") as f:
            lns = f.readlines()
            address = lns[0].rstrip('\n')
            private_key = lns[1].rstrip('\n')

    print("My address: {}".format(address))
    print("My private key: {}".format(private_key))

    return private_key, address


def get_algod_client(private_key, my_address):
    algod_address = "http://localhost:4001"
    algod_address = "https://node.testnet.algoexplorerapi.io"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(algod_token, algod_address)
    account_info = algod_client.account_info(my_address)
    print("Account balance: {} microAlgos\n".format(account_info.get('amount')))

    return algod_client


def main():
    gen_new_address = True
    # gen_new_address = False
    pvt_key, address = generate_algorand_keypair(gen_new_address)
    algod_client = get_algod_client(pvt_key, address)

    # ipdb.set_trace()
    # compile program to TEAL assembly
    # with open("./lsig.teal", "w") as f:
    #     lsig_teal = call_lsig()
    #     f.write(lsig_teal)

    data = open("./lsig.teal", 'r').read()
    # compile teal program
    response = algod_client.compile(data)
    programstr = response['result']
    t = programstr.encode()
    program = base64.decodebytes(t)

    arg_str = address
    arg1 = arg_str.encode()
    lsig = LogicSigAccount(program, args=[arg1])

    print("Lsig address: " + lsig.address())


main()
