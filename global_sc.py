from pyteal import *

'''
Opts in by creator and user
Creates box for self
    - <creator address> vs <3 digit generated idx>:<app id>:<10 bytes dapp name> 
Creates box for each new user and creator
During creator opt in
    - <creator address> vs <3 digit generated idx>:<10 bytes dapp name>
    - If opt in succeeds, creator creates creator-SC and registers app-id 
        - <creator address> vs <3 digit generated idx>:<app id>:<10 bytes dapp name>

'''
TYPE_DAPP = Bytes("dapp")
TYPE_USER = Bytes("user")
DAPP_COUNT = Bytes("dappcount")
DAPP_NAME_MAX_LEN = Int(10)
MSG_COUNT = Bytes("msgcount")
INDEX_KEY = Bytes("index")
MAX_BOX_SIZE = Int(32768)
MAX_LSTATE_SIZE = Int(16)
MAX_BOX_LEN = Int(32)
# dummy address that belongs to algo dispenser source account
NOTIBOY_ADDR = "HZ57J3K46JIJXILONBBZOHX6BKPXEM2VVXNRFSUED6DKFD5ZD24PMJ3MVA"
ERASE_BYTES = Bytes(
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
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


@Subroutine(TealType.bytes)
def sender_from_gstate(dapp_name):
    return Extract(
        App.globalGet(dapp_name), Int(0), Int(32)
    )


@Subroutine(TealType.bytes)
def index_from_gstate(dapp_name):
    return Seq(
        (idx := ScratchVar(TealType.bytes)).store(Extract(
            App.globalGet(dapp_name), Int(33), Int(1)
        )),
        idx.load()
    )


@Subroutine(TealType.uint64)
def is_valid_optout():
    return And(
        Eq(Gtxn[0].rekey_to(), Global.zero_address()),
        Eq(Gtxn[1].rekey_to(), Global.zero_address()),
        Eq(Gtxn[2].rekey_to(), Global.zero_address()),
        Eq(Gtxn[3].rekey_to(), Global.zero_address()),
        Eq(Global.group_size(), Int(4)),
        Eq(Gtxn[0].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[0].on_completion(), OnComplete.CloseOut),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[1].on_completion(), OnComplete.NoOp),
        Eq(Gtxn[2].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[2].on_completion(), OnComplete.NoOp),
        Eq(Gtxn[3].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[3].on_completion(), OnComplete.NoOp)
    )


@Subroutine(TealType.uint64)
def is_valid_optin():
    return And(
        Eq(Gtxn[0].rekey_to(), Global.zero_address()),
        Eq(Gtxn[1].rekey_to(), Global.zero_address()),
        Eq(Gtxn[2].rekey_to(), Global.zero_address()),
        Eq(Gtxn[3].rekey_to(), Global.zero_address()),
        Eq(Gtxn[4].rekey_to(), Global.zero_address()),
        Eq(Global.group_size(), Int(5)),
        Eq(Gtxn[0].type_enum(), TxnType.Payment),
        Eq(Gtxn[0].receiver(), Addr(NOTIBOY_ADDR)),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[1].on_completion(), OnComplete.OptIn),
        Eq(Gtxn[2].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[2].on_completion(), OnComplete.NoOp),
        Eq(Gtxn[3].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[3].on_completion(), OnComplete.NoOp),
        Eq(Gtxn[4].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[4].on_completion(), OnComplete.NoOp)
    )


@Subroutine(TealType.uint64)
def is_valid_private_notification():
    return And(
        Eq(Gtxn[0].rekey_to(), Global.zero_address()),
        Eq(Gtxn[1].rekey_to(), Global.zero_address()),
        Eq(Gtxn[2].rekey_to(), Global.zero_address()),
        Eq(Gtxn[3].rekey_to(), Global.zero_address()),
        Eq(Gtxn[4].rekey_to(), Global.zero_address()),
        Eq(Gtxn[0].application_args.length(), Int(2)),
        Eq(Gtxn[0].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[0].on_completion(), OnComplete.NoOp),
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[1].on_completion(), OnComplete.NoOp),
        Eq(Gtxn[2].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[2].on_completion(), OnComplete.NoOp),
        Eq(Gtxn[3].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[3].on_completion(), OnComplete.NoOp),
        Eq(Gtxn[4].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[4].on_completion(), OnComplete.NoOp),
        Eq(Global.group_size(), Int(5)),
        Eq(
            # verify dapp name belongs to sender
            # <txn sender> == dapp_name's acct addr in global state
            Gtxn[0].sender(),
            sender_from_gstate(Gtxn[0].application_args[1])
        ),
        # dapp opted in?
        Eq(App.optedIn(Gtxn[0].sender(), app_id), Int(1)),
    )


@Subroutine(TealType.uint64)
def is_valid_public_notification():
    return And(
        # should contain just 1 txn
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.application_args.length(), Int(2)),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Txn.type_enum(), TxnType.ApplicationCall),
        Eq(Txn.on_completion(), OnComplete.NoOp),
        Eq(
            # verify dapp name belongs to sender
            # <txn sender> == <gstate sender> in global state
            Txn.sender(),
            sender_from_gstate(Txn.application_args[1]),
        ),
        # dapp opted in?
        Eq(App.optedIn(Txn.sender(), app_id), Int(1)),
    )


@Subroutine(TealType.bytes)
def dapp_name(name):
    return (
        If(
            Len(name) > DAPP_NAME_MAX_LEN
        )
        .Then(
            Extract(name, Int(0), DAPP_NAME_MAX_LEN)
        )
        .Else(name)
    )


# invoked as part of dapp opt-in
# arg: "dapp" dapp_name
# global registry will have | dapp_name | <-> | sender_addr : dapp_count | mapping
# dapp_count acts as dap index
# grp txn - txn1 is payment, txn2 is app call
# Stores 64 128B key value pairs ( 1 reserved for dapp count)
@Subroutine(TealType.none)
def register_dapp():
    name = ScratchVar(TealType.bytes)
    next_dapp_idx = ScratchVar(TealType.bytes)
    dapp_count = ScratchVar(TealType.uint64)
    return Seq(
        # dapp name
        name.store(dapp_name(Gtxn[1].application_args[1])),
        val := App.globalGetEx(app_id, name.load()),
        # check if dapp name is already registered
        # Client should take care of case sensitivity
        Assert(Not(val.hasValue())),
        dapp_count.store(Btoi(App.globalGet(DAPP_COUNT))),
        next_dapp_idx.store(Itob(Add(dapp_count.load(), Int(1)))),
        Assert(
            And(
                Gtxn[1].application_args.length() == Int(2),
                Gtxn[1].application_args[0] == TYPE_DAPP,
                # amt is >= optin fee
                Ge(Gtxn[0].amount(), Int(DAPP_OPTIN_FEE)),
            )
        ),
        App.globalPut(name.load(), Concat(Gtxn[0].sender(), Bytes(":"), next_dapp_idx.load())),
        # update dapp count
        App.globalPut(DAPP_COUNT, next_dapp_idx.load()),
        # create box
        Assert(App.box_create(name.load(), MAX_BOX_SIZE)),
        Approve()
    )


# single txn from dapp creator
# 1. remove entry from global state
# 2. remove boxes
@Subroutine(TealType.none)
def deregister_dapp():
    name = ScratchVar(TealType.bytes)
    return Seq([
        # dapp name
        name.store(dapp_name(Gtxn[0].application_args[1])),
        val := App.globalGetEx(app_id, name.load()),
        If(
            And(
                val.hasValue(),
                Eq(
                    # extract sender address from global state for the given dapp name
                    Extract(val.value(), Int(0), Int(32)),
                    Txn.sender()
                ),
            )
        )
        .Then(
            Seq(
                App.globalDel(name.load()),
                Pop(App.box_delete(name.load()))
            )
        )
    ])


@Subroutine(TealType.none)
def deregister_user():
    return Seq(
        Assert(App.box_delete(Gtxn[0].sender())),
        Approve()
    )


# invoked as part of user opt-in
# arg: "user"
@Subroutine(TealType.none)
def register_user():
    return Seq([
        Assert(
            And(
                Gtxn[1].application_args.length() == Int(1),
                Gtxn[1].application_args[0] == TYPE_USER,
                # amt is >= optin fee
                Ge(Gtxn[0].amount(), Int(USER_OPTIN_FEE))
            )
        ),
        # create box with name as sender's 32B address
        Assert(App.box_create(Gtxn[0].sender(), MAX_BOX_SIZE)),
        Approve()
    ])


@Subroutine(TealType.uint64)
def is_verified():
    val = App.globalGet(Txn.application_args[1])
    return (
        If(
            Eq(
                Len(val), Int(65)
            )
        )
        .Then(Int(0))
        .ElseIf(
            And(
                Eq(
                    Len(val), Int(67)
                ),
                Eq(
                    Extract(val, Int(66), Int(1)), Bytes("v")
                )
            )
        )
        .Then(Int(1))
        .Else(Int(0))
    )


@Subroutine(TealType.uint64)
def verify_dapp_addr():
    val = App.globalGet(Txn.application_args[1])
    return Seq([
        Assert(
            And(
                Ge(Len(val), Int(65)),
                Eq(
                    Extract(val, Int(33), Int(32)), Txn.accounts[1]
                )
            )
        ),
        Approve()
    ])


@Subroutine(TealType.uint64)
def mark_dapp_verified():
    val = ScratchVar(TealType.bytes)
    return Seq([
        val.store(App.globalGet(Txn.application_args[1])),
        If(Not(is_verified()))
        .Then(
            Seq([
                App.globalDel(Txn.application_args[1]),
                App.globalPut(Txn.application_args[1],
                              Concat(
                                  val.load(), Bytes(":v"),
                              )
                              ),
                Approve()
            ])
        ),
        Approve()
    ])


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


@Subroutine(TealType.none)
def inc_msg_count(addr):
    return Seq([
        count_val := App.localGetEx(addr, app_id, MSG_COUNT),
        If(Not(count_val.hasValue()))
        .Then(App.localPut(addr, MSG_COUNT, Itob(Int(0)))),
        App.localPut(addr, MSG_COUNT, Itob(
            Add(
                Btoi(App.localGet(addr, MSG_COUNT)), Int(1)
            )
        ))
    ])


# initialise index to 0
@Subroutine(TealType.bytes)
def load_idx_from_lstate(addr):
    index_val = App.localGetEx(addr, app_id, INDEX_KEY)
    return Seq([
        index_val,
        If(Not(index_val.hasValue()))
        .Then(App.localPut(addr, INDEX_KEY, Itob(Int(0)))),
        App.localGet(addr, INDEX_KEY)
    ])


@Subroutine(TealType.uint64)
def min_val(x, y):
    return Seq(
        If(Gt(x, y))
        .Then(
            y
        )
        .Else(
            x
        )
    )


@Subroutine(TealType.bytes)
def construct_msg():
    # return Itob(Global.latest_timestamp())
    return Concat(
        Itob(Global.latest_timestamp()),
        Gtxn[0].application_args[1],
        Bytes(":"),
        Extract(Gtxn[0].note(), Int(0), min_val(Int(1008), Len(Gtxn[0].note()))),
    )


@Subroutine(TealType.none)
def write_msg(idx, msg):
    return Seq(
        (start_byte := ScratchVar(TealType.uint64)).store(Mul(Btoi(idx), Int(1024))),
        App.box_replace(Gtxn[0].accounts[1], start_byte.load(), Extract(ERASE_BYTES, Int(0), Len(ERASE_BYTES))),
        App.box_replace(Gtxn[0].accounts[1], start_byte.load(), msg)
    )


@Subroutine(TealType.none)
def user_optin_dapp(dapp_idx):
    return Seq(
        is_apps_set := App.localGetEx(Gtxn[0].accounts[1], app_id, Bytes("apps")),
        If(
            And(
                Eq(
                    is_apps_set.hasValue(), Int(0)
                ),
                Eq(
                    Btoi(is_apps_set.value()), Int(0)
                )
            )
        )
        .Then(App.localPut(Gtxn[0].accounts[1], Bytes("apps"), dapp_idx))
        .Else(
            (found := ScratchVar(TealType.uint64)).store(Int(0)),
            (app_list := ScratchVar(TealType.bytes)).store(App.localGet(Gtxn[0].accounts[1], Bytes("apps"))),
            For((start_idx := ScratchVar(TealType.uint64)).store(Int(0)),
                start_idx.load() < Len(app_list.load()),
                start_idx.store(start_idx.load() + Int(3))
                ).Do(
                If(
                    Eq(
                        Extract(app_list.load(), start_idx.load(), Int(3)),
                        dapp_idx
                    )
                )
                .Then(
                    found.store(Int(1)),
                    Break()
                )
            ),
            If(
                Neq(
                    found.load(),
                    Int(1)
                )
            )
            .Then(
                app_list.store(
                    Concat(app_list.load(), dapp_idx)
                )
            )
        )
    )


'''
app_args: pvt_notify dapp_name
acct_args: rcvr_addr
'''
private_notify = Seq([
    Assert(is_valid_private_notification()),
    # is rcvr address passed?
    Assert(Eq(Gtxn[0].accounts.length(), Int(1))),
    # rcvr opted in?
    Assert(App.optedIn(Txn.accounts[1], app_id)),

    # this ranges from 0 to 31
    (next_lstate_index := ScratchVar(TealType.bytes)).store(Itob(
        (Btoi(load_idx_from_lstate(Txn.accounts[1])) + Int(1)) % MAX_BOX_LEN
    )),
    App.localDel(Txn.accounts[1], next_lstate_index.load()),
    # set index key
    App.localPut(Txn.accounts[1], INDEX_KEY, next_lstate_index.load()),
    # increase 'sent' msg count of dapp
    inc_msg_count(Txn.sender()),
    # increase 'received' msg count of rcvr
    inc_msg_count(Txn.accounts[1]),
    (data := ScratchVar(TealType.bytes)).store(construct_msg()),
    write_msg(next_lstate_index.load(), data.load()),
    # user_optin_dapp(index_from_gstate(Gtxn[0].application_args[1])),
    Approve()
])

'''
app_args: pub_notify dapp_name
'''
public_notify = Seq([
    Assert(is_valid_public_notification()),
    # ranges from 0 to 15, but we don't 0th location as we store this index there
    (next_lstate_index := ScratchVar(TealType.bytes)).store(Itob(
        (Btoi(load_idx_from_lstate(Txn.sender())) + Int(1)) % MAX_LSTATE_SIZE
    )),
    If(Btoi(next_lstate_index.load()) == Int(0))
    .Then(next_lstate_index.store(Itob(Int(1)))),
    App.localDel(Txn.sender(), next_lstate_index.load()),
    # set index key
    App.localPut(Txn.sender(), INDEX_KEY, next_lstate_index.load()),
    App.localPut(Txn.sender(), next_lstate_index.load(), Txn.tx_id()),
    Approve()
])

handle_creation = Seq([
    Assert(is_valid()),
    App.globalPut(DAPP_COUNT, Itob(Int(100))),
    Approve()
])

# args: user/dapp <dapp_name if arg1 is dapp>
handle_optin = Seq([
    Assert(is_valid_optin()),
    If(
        And(
            Eq(Gtxn[1].application_args.length(), Int(2)),
            Gtxn[1].application_args[0] == TYPE_DAPP,
        )
    )
    .Then(register_dapp())
    .Else(register_user()),
    Approve()
])

# args: user/dapp <dapp_name if arg1 is dapp>
handle_optout = Seq([
    Assert(is_valid_optout()),
    If(
        And(
            Eq(Gtxn[0].application_args.length(), Int(2)),
            Gtxn[0].application_args[0] == TYPE_DAPP,
        )
    )
    .Then(deregister_dapp())
    .Else(deregister_user()),
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
