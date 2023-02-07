from sc.creator_registration import *
from sc.user_registration import *
from sc.creator_verify import *
from sc.messaging import *

'''
app_args: verify dapp_name index_position
acct_args: app_id
'''
unverify_dapp = Seq([
    Assert(is_channel_valid_for_verification()),
    Return(mark_channel_unverified())
])

'''
app_args: verify dapp_name index_position
acct_args: app_id
'''
verify_dapp = Seq([
    Assert(is_channel_valid_for_verification()),
    Return(mark_channel_verified())
])

'''
app_args: pvt_notify dapp_name
acct_args: rcvr_addr
'''
private_notify = Seq([
    Assert(is_valid_private_notification()),
    # Assert(is_pay_required()),
    send_personal_msg(),
    Approve()
])

'''
app_args: pub_notify dapp_name
'''
public_notify = Seq([
    Assert(is_valid_public_notification()),
    send_public_msg(),
    Approve()
])

# Bootstraps Notiboy SC
# Stores dapp count in global state
# Creates main box
bootstrap = Seq([
    Assert(
        And(
            is_valid(),
            is_creator()
        )
    ),
    App.globalPut(INDEX_KEY, Itob(Int(0))),
    App.globalPut(MSG_COUNT, Concat(Itob(Int(0)), DELIMITER, Itob(Int(0)))),
    App.globalPut(OPTIN_COUNT, Concat(Itob(Int(0)), DELIMITER, Itob(Int(0)))),
    # create box
    Assert(Le(App.box_create(NOTIBOY_BOX, MAX_MAIN_BOX_SIZE), Int(1))),
    # setting zero value
    For((start_idx := ScratchVar(TealType.uint64)).store(Int(0)),
        And(
            start_idx.load() < Int(32),
            Mul(start_idx.load(), Int(1024)) < MAX_MAIN_BOX_SIZE
        ),
        start_idx.store(start_idx.load() + Int(1))
        ).Do(
        App.box_replace(NOTIBOY_BOX, Mul(start_idx.load(), Int(1024)),
                        Extract(ERASE_BYTES, Int(0), Int(1024))),
    ),
    Approve()
])

# Note: used only for testing
dev_test = Seq([
    Assert(
        And(
            is_valid(),
            is_creator()
        )
    ),
    Pop(App.box_delete(NOTIBOY_BOX)),
    Approve()
])

# Creates Notiboy SC
handle_creation = Seq([
    Assert(is_valid()),
    Approve()
])

# This is a group txn where first txn is payment and second is app call
# args:
# 1. user/dapp
# 2. <dapp_name> if arg0 is dapp
# 3. <app_id> if arg0 is dapp
# acct args:
# 1. <app_id> if arg0 is dapp
handle_optin = Seq([
    Assert(is_valid_base_optin()),
    If(
        And(
            Eq(Gtxn[1].application_args.length(), Int(2)),
            Eq(Gtxn[1].applications.length(), Int(1)),
            Gtxn[1].application_args[0] == TYPE_DAPP,
        )
    )
    .Then(
        Assert(is_valid_creator_optin()),
        register_dapp()
    )
    .Else(
        Assert(is_valid_user_optin()),
        register_user()
    ),
    Approve()
])

# args:
# 1. user/dapp
# 2. <dapp_name> if arg0 is dapp
# 3. <app_id> if arg0 is dapp
# acct args:
# 1. <app_id> if arg0 is dapp
handle_optout = Seq([
    Assert(is_valid_base_optout()),
    If(
        And(
            Eq(Gtxn[0].application_args.length(), Int(3)),
            Eq(Gtxn[0].applications.length(), Int(1)),
            Gtxn[0].application_args[0] == TYPE_DAPP,
        )
    )
    .Then(
        Assert(is_valid_creator_optout()),
        deregister_dapp()
    )
    .Else(
        Assert(is_valid_user_optout()),
        deregister_user()
    ),
    Approve()
])

# txn can update the app only if initiated by creator
handle_updateapp = Seq([
    Assert(is_valid()),
    Return(is_creator())
])
# no txn should delete the app
handle_deleteapp = Seq([
    Assert(is_valid()),
    Return(is_creator())
])

# this is for dummy box budget txns
noop_dummies = Seq([
    validate_rekeys(Int(0), Int(0)),
    Approve()
])

# application calls
handle_noop = Seq([
    Cond(
        [Txn.application_args.length() == Int(0), noop_dummies],
        [Txn.application_args[0] == Bytes("bootstrap"), bootstrap],
        [Txn.application_args[0] == Bytes("test"), dev_test],
        [Txn.application_args[0] == Bytes("pub_notify"), public_notify],
        [Txn.application_args[0] == Bytes("pvt_notify"), private_notify],
        [Txn.application_args[0] == Bytes("verify"), verify_dapp],
        [Txn.application_args[0] == Bytes("unverify"), unverify_dapp]
    )
])


def approval_program():
    program = Cond(
        [Txn.application_id() == Int(0), handle_creation],
        [Txn.on_completion() == OnComplete.OptIn, handle_optin],
        [Txn.on_completion() == OnComplete.CloseOut, handle_optout],
        [Txn.on_completion() == OnComplete.UpdateApplication, handle_updateapp],
        [Txn.on_completion() == OnComplete.DeleteApplication, handle_deleteapp],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop]
    )

    return compileTeal(program, Mode.Application, version=8)


def clear_state_program():
    program = Cond(
        [Txn.on_completion() == OnComplete.ClearState, handle_optout]
    )
    return compileTeal(program, Mode.Application, version=8)
