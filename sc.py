from pyteal import *

OPTIN_TYPE_DAPP = "dapp"
OPTIN_TYPE_USER = "user"
INDEX_KEY = "index"
# dummy address that belongs to algo dispenser source account
NOTIBOY_ADDR = "HZ57J3K46JIJXILONBBZOHX6BKPXEM2VVXNRFSUED6DKFD5ZD24PMJ3MVA"
# 1 algo
DAPP_OPTIN_FEE = 1000000
# 1 algo
USER_OPTIN_FEE = 1000000

is_creator = Assert(Txn.sender() == Global.creator_address())
app_id = Global.current_application_id()


@Subroutine(TealType.uint64)
def is_creator():
    return Eq(Txn.sender(), Global.creator_address())


@Subroutine(TealType.uint64)
def is_valid():
    return And(
        Eq(Txn.rekey_to(), Global.zero_address())
    )


@Subroutine(TealType.uint64)
def is_valid_optin():
    return And(
        And(
            Eq(Gtxn[0].rekey_to(), Global.zero_address()),
            Eq(Gtxn[1].rekey_to(), Global.zero_address()),
            Eq(Global.group_size(), Int(2)),
            Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
            Eq(Gtxn[1].on_completion(), OnComplete.OptIn),
            Eq(Gtxn[0].type_enum(), TxnType.Payment),
            Eq(Gtxn[0].receiver(), Addr(NOTIBOY_ADDR))
        )
    )


# invoked as part of dapp opt-in
# arg: "dapp" dapp_name
# global registry will have dapp_name <-> sender_addr mapping
@Subroutine(TealType.uint64)
def register_dapp():
    return Seq([
        Assert(
            And(
                Gtxn[1].application_args.length() == Int(2),
                Gtxn[1].application_args[0] == Bytes(OPTIN_TYPE_DAPP),
                # amt is >= optin fee
                Ge(Gtxn[0].amount(), Int(DAPP_OPTIN_FEE)),
                # check if dapp name is already registered
                # Client should take care of case sensitivity
                Eq(App.globalGet(Gtxn[1].application_args[1]), Bytes(""))
            )
        ),
        App.globalPut(Gtxn[1].application_args[1], Gtxn[1].sender()),
        Approve()
    ])


# invoked as part of user opt-in
# arg: "user"
@Subroutine(TealType.uint64)
def register_user():
    return Seq([
        Assert(
            And(
                Gtxn[1].application_args.length() == Int(1),
                Gtxn[1].application_args[0] == Bytes(OPTIN_TYPE_USER),
                # amt is >= optin fee
                Ge(Gtxn[0].amount(), Int(USER_OPTIN_FEE))
            )
        ),
        Approve()
    ])


@Subroutine(TealType.bytes)
def load_index():
    # initialise index to 0
    # working range is 1 to 15
    # The 0th slot is used for storing index
    # index points to the latest txn
    index_val = App.localGetEx(Txn.sender(), app_id, Bytes(INDEX_KEY))
    return Seq([
        index_val,
        If(Not(index_val.hasValue()))
        .Then(App.localPut(Txn.sender(), Bytes(INDEX_KEY), Itob(Int(0)))),
        App.localGet(Txn.sender(), Bytes(INDEX_KEY))
    ])


'''
args: pvt_notify rcvr_addr dapp_name
'''
private_notify = Seq([
    # dapp opted in?
    Assert(App.optedIn(Txn.sender(), app_id)),
    # rcvr opted in?
    Assert(App.optedIn(Txn.application_args[1], app_id)),
    # sender opted in?
    Assert(App.optedIn(Txn.sender(), app_id)),
    Assert(is_valid()),
    # verify dapp_name belongs to sender
    Assert(
        Eq(
            App.globalGet(Txn.application_args[2]), Txn.sender()
        )
    ),
    # delete existing pvt notification, key as dapp_name
    App.localDel(Txn.application_args[1], Txn.application_args[2]),
    # key dapp_name, value as txn_id
    App.localPut(Txn.application_args[1], Txn.application_args[2], Txn.tx_id()),
    Approve()
])

next_index = ScratchVar(TealType.bytes)

public_notify = Seq([
    Assert(App.optedIn(Txn.sender(), app_id)),
    Assert(is_valid()),
    next_index.store(Itob(
        (Btoi(load_index()) + Int(1)) % Int(16)
    )),
    If(Btoi(next_index.load()) == Int(0))
    .Then(next_index.store(Itob(Int(1)))),
    App.localDel(Txn.sender(), next_index.load()),
    App.localPut(Txn.sender(), next_index.load(), Txn.tx_id()),
    App.localPut(Txn.sender(), Bytes(INDEX_KEY), next_index.load()),
    Approve()
])

handle_creation = Seq([
    Assert(is_valid()),
    App.globalPut(Bytes("Creator"), Bytes("Deepak")),
    Approve()
])

# args: user/dapp <dapp_name if arg1 is dapp>
handle_optin = Seq([
    Assert(is_valid_optin()),
    If(
        And(
            Ge(Gtxn[1].application_args.length(), Int(1)),
            Gtxn[1].application_args[0] == Bytes(OPTIN_TYPE_DAPP),
        )
    )
    .Then(Pop(register_dapp()))
    .Else(Pop(register_user())),
    Approve()
])
# no txn should clear the local state
handle_closeout = Seq([
    Assert(is_valid()),
    Reject()
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
        [Txn.application_args[0] == Bytes("Notify"), public_notify],
        [Txn.application_args[0] == Bytes("pvt_notify"), private_notify]
    )
])


def approval_program():
    program = Cond(
        [Txn.application_id() == Int(0), handle_creation],
        [Txn.on_completion() == OnComplete.OptIn, handle_optin],
        [Txn.on_completion() == OnComplete.CloseOut, handle_closeout],
        [Txn.on_completion() == OnComplete.UpdateApplication, handle_updateapp],
        [Txn.on_completion() == OnComplete.DeleteApplication, handle_deleteapp],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop]
    )

    return compileTeal(program, Mode.Application, version=6)


def clear_state_program():
    program = Return(Int(1))
    return compileTeal(program, Mode.Application, version=6)
