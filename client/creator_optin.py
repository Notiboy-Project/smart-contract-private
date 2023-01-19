from client.lib.util import compile_program, read_global_state, DAPP_NAME, APP_ID, generate_creator_algorand_keypair, \
    get_algod_client, read_global_state_key, read_local_state, \
    MAIN_BOX, print_main_box
from launch_sc import create_app
from client.lib.opt import opt_in, opt_out
from client.lib.constants import *
from client.message import send_public_notification
from algosdk.future import transaction
from creator_sc import clear_state_program, approval_program


def create_creator_app():
    pvt_key, address = generate_creator_algorand_keypair()
    algod_client = get_algod_client(address)

    # declare application state storage (immutable)
    # 16 local kv pairs, each pair 128 bytes
    local_ints = 0
    local_bytes = 16
    local_schema = transaction.StateSchema(local_ints, local_bytes)
    # 64 global kv pairs, each pair 128 bytes
    global_ints = 0
    global_bytes = 64
    global_schema = transaction.StateSchema(global_ints, global_bytes)

    # compile program to TEAL assembly
    with open("./approval.teal", "w") as f:
        approval_program_teal = approval_program()
        f.write(approval_program_teal)

    # compile program to TEAL assembly
    with open("./clear.teal", "w") as f:
        clear_state_program_teal = clear_state_program()
        f.write(clear_state_program_teal)

    # compile program to binary
    approval_program_compiled = compile_program(algod_client, approval_program_teal)

    # compile program to binary
    clear_state_program_compiled = compile_program(algod_client, clear_state_program_teal)

    print("Deploying Creator application......")

    # create new application
    app_id = create_app(algod_client, pvt_key, approval_program_compiled, clear_state_program_compiled,
                        global_schema, local_schema)
    print("Creator APP ID:", app_id)


def creator_optin():
    print("\n*************CREATOR OPT-IN START*************")
    pvt_key, address = generate_creator_algorand_keypair()
    algod_client = get_algod_client(address)

    # create test.teal with following
    # #pragma version 7
    # int 1
    # ./sandbox copyTo test.teal
    # WARN: should be strictly 64 global byteslices and 16 local byteslices
    # ./sandbox goal app create --creator EVYC4CFP533BRC26OLGJEWJJ4SDB5JZJPNFPOZ7R56QUENTTUDQDLNJGTM --global-byteslices 64 --global-ints 0 --local-byteslices 16 --local-ints 0 --approval-prog test.teal  --clear-prog test.teal
    # Pass created app id as arg
    num_noops = 4
    dapp_name = DAPP_NAME
    app_args = [
        str.encode("dapp"),
        str.encode(dapp_name),
    ]

    foreign_apps = [
        CREATOR_APP_ID
    ]
    acct_args = []
    try:
        opt_in(algod_client, pvt_key, APP_ID, MAIN_BOX, app_args, acct_args, foreign_apps, num_noops)
    except Exception as err:
        print("error opting in, err: {}".format(err))
    read_local_state(algod_client, address, APP_ID)
    print_main_box(algod_client, APP_ID, "notiboy".encode('utf-8'))
    print("*************CREATOR OPT-IN END*************")


def creator_optout():
    print("\n*************CREATOR OPT-OUT START*************")
    pvt_key, address = generate_creator_algorand_keypair()
    algod_client = get_algod_client(address)

    # create test.teal with following
    # #pragma version 7
    # int 1
    # ./sandbox copyTo test.teal
    # WARN: should be strictly 64 global byteslices and 16 local byteslices
    # ./sandbox goal app create --creator EVYC4CFP533BRC26OLGJEWJJ4SDB5JZJPNFPOZ7R56QUENTTUDQDLNJGTM --global-byteslices 64 --global-ints 0 --local-byteslices 16 --local-ints 0 --approval-prog test.teal  --clear-prog test.teal
    # Pass created app id as arg
    num_noops = 4
    dapp_name = DAPP_NAME
    app_args = [
        str.encode("dapp"),
        str.encode(dapp_name),
    ]

    foreign_apps = [
        CREATOR_APP_ID
    ]
    acct_args = []

    # OPT OUT
    nxt_idx = read_global_state_key(algod_client, APP_ID, "index")
    app_args.append(
        # passing index to preventing for loop in SC in order to clear outmain box slot
        (nxt_idx).to_bytes(8, 'big')
    )
    try:
        opt_out(algod_client, pvt_key, APP_ID, MAIN_BOX, app_args, acct_args, foreign_apps, num_noops)
    except Exception as err:
        print("error opting out, err: {}".format(err))
    read_local_state(algod_client, address, APP_ID)
    print_main_box(algod_client, APP_ID, "notiboy".encode('utf-8'))

    print("Global state:", read_global_state(algod_client, APP_ID))
    print("*************CREATOR OPT-OUT END*************")
