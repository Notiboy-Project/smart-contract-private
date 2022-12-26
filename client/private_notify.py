from algosdk import account
from algosdk import encoding
from algosdk.future import transaction

from client.lib.util import read_local_state, read_global_state, get_algod_client, DAPP_NAME, APP_ID, \
    generate_algorand_keypair, \
    NOTIBOY_ADDR


def opt_out(client, private_key, index, dapp_name):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("OptOut from account: ", sender)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    if dapp_name == "":
        app_args = [
            str.encode("user"),
        ]
        boxes = [
            # use public key as box name
            [0, encoding.decode_address(sender)],
            [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""]
        ]
    else:
        app_args = [
            str.encode("dapp"),
            str.encode(dapp_name),
        ]
        boxes = [
            [0, dapp_name],
            [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""]
        ]

    print("app_args: ", app_args)

    # create unsigned transaction
    txn2 = transaction.ApplicationCloseOutTxn(sender, params, index, app_args, boxes=boxes)
    txn3 = transaction.ApplicationNoOpTxn(sender, params, index, note="txn3", boxes=boxes)
    txn4 = transaction.ApplicationNoOpTxn(sender, params, index, note="txn4", boxes=boxes)
    txn5 = transaction.ApplicationNoOpTxn(sender, params, index, note="txn5", boxes=boxes)

    gid = transaction.calculate_group_id([txn2, txn3, txn4, txn5])
    transaction.assign_group_id([txn2, txn3, txn4, txn5])
    txn2.gid = gid
    txn3.gid = gid
    txn4.gid = gid
    txn5.gid = gid

    # sign transaction
    signed_txn2 = txn2.sign(private_key)
    signed_txn3 = txn3.sign(private_key)
    signed_txn4 = txn4.sign(private_key)
    signed_txn5 = txn5.sign(private_key)
    signed_group = [signed_txn2, signed_txn3, signed_txn4, signed_txn5]

    # send transaction
    tx_id = client.send_transactions(signed_group)

    # await confirmation
    transaction.wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("OptOut from app-id: {} in round: {}".format(index, transaction_response.get("confirmed-round")))


def opt_in(client, private_key, index, dapp_name):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("OptIn from account: ", sender)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    if dapp_name == "":
        app_args = [
            str.encode("user"),
        ]
        boxes = [
            # use public key as box name
            [0, encoding.decode_address(sender)],
            [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""]
        ]
    else:
        app_args = [
            str.encode("dapp"),
            str.encode(dapp_name),
        ]
        boxes = [
            [0, dapp_name],
            [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""]
        ]

    print("app_args: ", app_args)

    # create unsigned transaction
    txn2 = transaction.ApplicationOptInTxn(sender, params, index, app_args, boxes=boxes)
    txn3 = transaction.ApplicationNoOpTxn(sender, params, index, note="txn3", boxes=boxes)
    txn4 = transaction.ApplicationNoOpTxn(sender, params, index, note="txn4", boxes=boxes)
    txn5 = transaction.ApplicationNoOpTxn(sender, params, index, note="txn5", boxes=boxes)

    # pay 1 algo
    txn1 = transaction.PaymentTxn(sender, params, NOTIBOY_ADDR,
                                  1000000)

    gid = transaction.calculate_group_id([txn1, txn2, txn3, txn4, txn5])
    transaction.assign_group_id([txn1, txn2, txn3, txn4, txn5])
    txn1.gid = gid
    txn2.gid = gid
    txn3.gid = gid
    txn4.gid = gid
    txn5.gid = gid

    # sign transaction
    signed_txn1 = txn1.sign(private_key)
    signed_txn2 = txn2.sign(private_key)
    signed_txn3 = txn3.sign(private_key)
    signed_txn4 = txn4.sign(private_key)
    signed_txn5 = txn5.sign(private_key)
    signed_group = [signed_txn1, signed_txn2, signed_txn3, signed_txn4, signed_txn5]

    # send transaction
    tx_id = client.send_transactions(signed_group)

    # await confirmation
    transaction.wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("OptIn to app-id: {} in round: {}".format(index, transaction_response.get("confirmed-round")))


def call_app(client, private_key, index, msg, app_args, acct_args):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("Call from account:", sender)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000
    boxes = [
        # use public key as box name
        [0, encoding.decode_address(acct_args[0])],
        [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""], [0, ""]
    ]
    # create unsigned transaction
    txn1 = transaction.ApplicationNoOpTxn(sender, params, index, app_args, acct_args, note=str.encode(msg))
    txn2 = transaction.ApplicationNoOpTxn(sender, params, index, note="txn3", boxes=boxes)
    txn3 = transaction.ApplicationNoOpTxn(sender, params, index, note="txn4", boxes=boxes)
    txn4 = transaction.ApplicationNoOpTxn(sender, params, index, note="txn6", boxes=boxes)
    txn5 = transaction.ApplicationNoOpTxn(sender, params, index, note="txn7", boxes=boxes)

    gid = transaction.calculate_group_id([txn1, txn2, txn3, txn4, txn5])
    transaction.assign_group_id([txn1, txn2, txn3, txn4, txn5])
    txn1.gid = gid
    txn2.gid = gid
    txn3.gid = gid
    txn4.gid = gid
    txn5.gid = gid

    # sign transaction
    signed_txn1 = txn1.sign(private_key)
    signed_txn2 = txn2.sign(private_key)
    signed_txn3 = txn3.sign(private_key)
    signed_txn4 = txn4.sign(private_key)
    signed_txn5 = txn5.sign(private_key)
    signed_group = [signed_txn1, signed_txn2, signed_txn3, signed_txn4, signed_txn5]

    # send transaction
    tx_id = client.send_transactions(signed_group)

    # await confirmation
    transaction.wait_for_confirmation(client, tx_id)
    print("Transaction ID:", tx_id)


def pvt_notify():
    pvt_key, rcvr_address = generate_algorand_keypair(overwrite=False, fname="rcvr-secret.txt", sandbox=False)
    algod_client = get_algod_client(pvt_key, rcvr_address)

    try:
        pass
        # opt_in(algod_client, pvt_key, APP_ID, "")
        # opt_out(algod_client, pvt_key, APP_ID, "")
    except Exception as err:
        print("error opting in, err: {}".format(err))

    msg = "hello, my name is Deepak"
    print("Sending private notification --> {}".format(msg))

    try:
        pvt_key, address = generate_algorand_keypair(overwrite=False, fname="sndr-secret.txt", sandbox=False)
        algod_client = get_algod_client(pvt_key, address)

        app_args = [
            str.encode("pvt_notify"),
            str.encode(DAPP_NAME),
        ]
        acct_args = [
            rcvr_address
        ]
        call_app(algod_client, pvt_key, APP_ID, msg, app_args, acct_args)
    except Exception as err:
        print("error calling app, err: {}".format(err))

    print("Local state of receiver ", rcvr_address)
    local_state = read_local_state(algod_client, rcvr_address, APP_ID)

    for k, v in local_state.items():
        print("{} --> {}".format(k, v))

    print("Global state:", read_global_state(algod_client, APP_ID))


def main():
    pvt_notify()


main()