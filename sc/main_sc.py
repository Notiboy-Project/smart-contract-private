from sc.creator_registration import *
from sc.user_registration import *
from sc.creator_verify import *
from sc.messaging import *

'''
app_args: verify dapp_name
acct_args: dapp_lsig_addr
'''
verify_dapp = Seq([
    Assert(
        And(
            is_valid(),
            Eq(Txn.application_args.length(), Int(2)),
            # is dapp lsig address passed?
            Eq(Txn.accounts.length(), Int(1)),
            # dapp lsig opted in?
            App.optedIn(Txn.accounts[1], app_id),
            # called by creator?
            is_creator(),
            # value should be at least 65 bytes long
            Ge(Len(App.globalGet(Txn.application_args[1])), Int(65)),
            # dapp lsig address present in global state against dapp name?
            Eq(
                Extract(App.globalGet(Txn.application_args[1]), Int(33), Int(32)), Txn.accounts[1]
            )
        )
    ),
    Return(mark_dapp_verified())
])

# to store list of dapps opted in by user
# @Subroutine(TealType.none)
# def user_optin_dapp(dapp_idx):
#     return Seq(
#         is_apps_set := App.localGetEx(Gtxn[0].accounts[1], app_id, Bytes("apps")),
#         If(
#             And(
#                 Eq(
#                     is_apps_set.hasValue(), Int(0)
#                 ),
#                 Eq(
#                     Btoi(is_apps_set.value()), Int(0)
#                 )
#             )
#         )
#         .Then(App.localPut(Gtxn[0].accounts[1], Bytes("apps"), dapp_idx))
#         .Else(
#             (found := ScratchVar(TealType.uint64)).store(Int(0)),
#             (app_list := ScratchVar(TealType.bytes)).store(App.localGet(Gtxn[0].accounts[1], Bytes("apps"))),
#             For((start_idx := ScratchVar(TealType.uint64)).store(Int(0)),
#                 start_idx.load() < Len(app_list.load()),
#                 start_idx.store(start_idx.load() + Int(3))
#                 ).Do(
#                 If(
#                     Eq(
#                         Extract(app_list.load(), start_idx.load(), Int(3)),
#                         dapp_idx
#                     )
#                 )
#                 .Then(
#                     found.store(Int(1)),
#                     Break()
#                 )
#             ),
#             If(
#                 Neq(
#                     found.load(),
#                     Int(1)
#                 )
#             )
#             .Then(
#                 app_list.store(
#                     Concat(app_list.load(), dapp_idx)
#                 )
#             )
#         )
#     )


'''
app_args: pvt_notify dapp_name
acct_args: rcvr_addr
'''
private_notify = Seq([
    # Assert(is_valid_private_notification()),
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
        is_valid(),
        is_creator()
    ),
    App.globalPut(INDEX_KEY, Itob(Int(0))),
    # create box
    Assert(App.box_create(NOTIBOY_BOX, MAX_BOX_SIZE)),
    # setting zero value
    For((start_idx := ScratchVar(TealType.uint64)).store(Int(0)),
        start_idx.load() < Int(32),
        start_idx.store(start_idx.load() + Int(1))
        ).Do(
        App.box_replace(NOTIBOY_BOX, Mul(start_idx.load(), Int(1024)), Extract(ERASE_BYTES, Int(0), Int(1024))),
    ),
    Approve()
])

# Note: used only for testing
dev_test = Seq([
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

# application calls
handle_noop = Seq([
    Cond(
        # this is for dummy box budget txns
        # TODO: add rekeying checks here
        [Txn.application_args.length() == Int(0), Approve()],
        [Txn.application_args[0] == Bytes("bootstrap"), bootstrap],
        [Txn.application_args[0] == Bytes("test"), dev_test],
        [Txn.application_args[0] == Bytes("pub_notify"), public_notify],
        [Txn.application_args[0] == Bytes("pvt_notify"), private_notify],
        [Txn.application_args[0] == Bytes("verify"), verify_dapp]
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
