from pyteal import *

USER_TYPE_DAPP = "dapp"
INDEX_KEY = "index"
# dummy address that belongs to algo dispenser source account
NOTIBOY_ADDR = "HZ57J3K46JIJXILONBBZOHX6BKPXEM2VVXNRFSUED6DKFD5ZD24PMJ3MVA"
# 1 algo
OPTIN_FEE = 1000000

is_creator = Assert(Txn.sender() == Global.creator_address())
app_id = Global.current_application_id()


@Subroutine(TealType.uint64)
def is_creator():
    return Eq(Txn.sender(), Global.creator_address())


@Subroutine(TealType.uint64)
def is_valid():
    return And(
        # not a group txn
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address())
    )


@Subroutine(TealType.uint64)
def is_valid_optin1():
    return Seq([
        Assert(
            And(
                Eq(Gtxn[0].rekey_to(), Global.zero_address()),
                Eq(Gtxn[1].rekey_to(), Global.zero_address()),
                Eq(Global.group_size(), Int(2)),
                Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
                Eq(Gtxn[1].on_completion(), OnComplete.OptIn),
                Eq(Gtxn[0].type_enum(), TxnType.Payment),
                Eq(Gtxn[0].receiver(), Addr(NOTIBOY_ADDR)),
                Ge(Gtxn[0].amount(), Int(OPTIN_FEE))
            )
        ),
        Approve()
    ])


@Subroutine(TealType.uint64)
def is_valid_optin():
    return And(
        Eq(Gtxn[0].rekey_to(), Global.zero_address()),
        Eq(Gtxn[1].rekey_to(), Global.zero_address()),
        Eq(Global.group_size(), Int(2)),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[1].on_completion(), OnComplete.OptIn),
        Eq(Gtxn[0].type_enum(), TxnType.Payment),
        Eq(Gtxn[0].receiver(), Addr(NOTIBOY_ADDR)),
        Ge(Gtxn[0].amount(), Int(OPTIN_FEE))
    )


# invoked as part of dapp opt-in
@Subroutine(TealType.uint64)
def register_dapp():
    return Seq([
        Assert(Gtxn[1].application_args.length() == Int(2)),
        App.globalPut(Gtxn[1].application_args[0], Gtxn[1].sender()),
        App.globalPut(Bytes("test"), Bytes("test")),
        Assert(Gtxn[1].application_args[1] == Bytes(USER_TYPE_DAPP)),
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


next_index = ScratchVar(TealType.bytes)

notify = Seq([
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

handle_optin = Seq([
    Assert(is_valid_optin()),
    Pop(register_dapp()),
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
        [Txn.application_args[0] == Bytes("Notify"), notify]
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
