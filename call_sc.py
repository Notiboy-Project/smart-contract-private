import base64

from algosdk.future import transaction
from algosdk import account, mnemonic
from algosdk.v2client import algod
from pyteal import compileTeal, Mode
from datetime import datetime,timezone
from zoneinfo import ZoneInfo

APP_ID = "94241155"

# # Read a file
# def load_resource(res):
#     dir_path = os.path.dirname(os.path.realpath(__file__))
#     path = os.path.join(dir_path, res)
#     with open(path, "rb") as fin:
#         data = fin.read()
#     return data
#
#
# def contract_account_example():
#     # Create an algod client
#     algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
#     algod_address = "https://node.testnet.algoexplorerapi.io"
#     receiver = "NQMDAY2QKOZ4ZKJLE6HEO6LTGRJHP3WQVZ5C2M4HKQQLFHV5BU5AW4NVRY"
#     algod_client = algod.AlgodClient(algod_token, algod_address)
#     myprogram = "logic-sig.teal"
#     # Read TEAL program
#     data = load_resource(myprogram)
#     source = data.decode('utf-8')
#     response = algod_client.compile(source)
#     print("Response Result = ", response['result'])
#     print("Response Hash = ", response['hash'])
#     # Create logic sig
#     programstr = response['result']
#     t = programstr.encode("ascii")
#     print("Encoded before %s, after %s", programstr, t)
#     # program = b"hex-encoded-program"
#     program = base64.decodebytes(t)
#     print(program)
#     print(len(program) * 8)
#     # string parameter
#     # arg_str = "<my string>"
#     # arg1 = arg_str.encode()
#     # lsig = transaction.LogicSig(program, args=[arg1])
#     # see more info here: https://developer.algorand.org/docs/features/asc1/sdks/#accessing-teal-program-from-sdks
#     # Create arg to pass if TEAL program requires an arg
#     # if not, omit args param
#     arg1 = (123).to_bytes(8, 'big')
#     lsig = LogicSig(program, args=[arg1])
#     sender = lsig.address()
#     # Get suggested parameters
#     params = algod_client.suggested_params()
#     # Comment out the next two (2) lines to use suggested fees
#     # params.flat_fee = True
#     # params.fee = 1000
#     # Build transaction
#     amount = 10000
#     closeremainderto = None
#     # Create a transaction
#     txn = PaymentTxn(
#         sender, params, receiver, amount, closeremainderto)
#     # Create the LogicSigTransaction with contract account LogicSig
#     lstx = transaction.LogicSigTransaction(txn, lsig)
#     # transaction.write_to_file([lstx], "simple.stxn")
#     # Send raw LogicSigTransaction to network
#     txid = algod_client.send_transaction(lstx)
#     print("Transaction ID: " + txid)
#     # wait for confirmation
#     try:
#         confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
#         print("TXID: ", txid)
#         print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))
#     except Exception as err:
#         print(err)
#     print("Transaction information: {}".format(
#         json.dumps(confirmed_txn, indent=4)))


# opt-in to application
def opt_in_app(client, private_key, index):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("OptIn from account: ", sender)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    # create unsigned transaction
    txn = transaction.ApplicationOptInTxn(sender, params, index)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    transaction.wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("OptIn to app-id:", transaction_response["txn"]["txn"]["apid"])


# call application
def call_app(client, private_key, index, msg):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("Call from account:", sender)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    app_args = [
        str.encode("Notify"),
    ]

    # create unsigned transaction
    txn = transaction.ApplicationNoOpTxn(sender, params, index, app_args, note=str.encode(msg))

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    transaction.wait_for_confirmation(client, tx_id)


def generate_algorand_keypair():
    # private_key, address = account.generate_account()
    # print("My address: {}".format(address))
    # print("My private key: {}".format(private_key))
    # print("My passphrase: {}".format(mnemonic.from_private_key(private_key)))

    private_key = "jTDuUq3AFTJBkmOQGLlB3mVnmvmUHQfxgEw/bs+XOO5ILNWQqI/QPl2a+VPDU78TeHBlZiTs7TfqPEjdm9wYoQ=="
    address = "JAWNLEFIR7ID4XM27FJ4GU57CN4HAZLGETWO2N7KHREN3G64DCQ37HJ5UU"

    return private_key, address


def get_algod_client(private_key, my_address):
    algod_address = "http://localhost:4001"
    # algod_address = "https://node.testnet.algoexplorerapi.io"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(algod_token, algod_address)
    account_info = algod_client.account_info(my_address)
    print("Account balance: {} microAlgos\n".format(account_info.get('amount')))

    return algod_client


# read user local state
def read_local_state(client, addr, app_id):
    results = client.account_info(addr)
    for local_state in results["apps-local-state"]:
        if local_state["id"] == app_id:
            if "key-value" not in local_state:
                return {}
            return format_state(local_state["key-value"])
    return {}


# helper function that formats global state for printing
def format_state(state):
    formatted = {}
    for item in state:
        key = item['key']
        value = item['value']
        formatted_key = base64.b64decode(key).decode('utf-8')
        if value['type'] == 1:
            # byte string
            if formatted_key == 'voted':
                formatted_value = base64.b64decode(value['bytes']).decode('utf-8')
            else:
                formatted_value = value['bytes']
            formatted[formatted_key] = formatted_value
        else:
            # integer
            formatted[formatted_key] = value['uint']
    return formatted


def main():
    pvt_key, address = generate_algorand_keypair()
    algod_client = get_algod_client(pvt_key, address)

    # opt_in_app(algod_client, pvt_key, APP_ID)

    msg = datetime.now(ZoneInfo('Asia/Kolkata')).strftime("%m/%d/%Y, %H:%M:%S")
    print("Sending notification --> {}".format(msg))
    call_app(algod_client, pvt_key, APP_ID, msg)

    read_local_state(algod_client, address, APP_ID)

main()