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
NOTIBOY_BOX = Bytes("notiboy")
MSG_COUNT = Bytes("msgcount")
INDEX_KEY = Bytes("index")
DELIMITER = Bytes(":")
DAPP_NAME_MAX_LEN = Int(10)
MAX_BOX_SIZE = Int(32768)
MAX_LSTATE_SIZE = Int(16)
MAX_USER_BOX_LEN = Int(32)
MAX_MAIN_BOX_MSG_SIZE = Int(26)
MAX_MAIN_BOX_NUM_CHUNKS = Div(MAX_BOX_SIZE, MAX_MAIN_BOX_MSG_SIZE)

# dummy address that belongs to algo dispenser source account
NOTIBOY_ADDR = "3KOQUDTQAYKMXFL66Q5DS27FJJS6O3E2J3YMOC3WJRWNWJW3J4Q65POKPI"
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
def is_valid_base_optout():
    return And(
        Eq(Gtxn[0].rekey_to(), Global.zero_address()),
        Eq(Gtxn[1].rekey_to(), Global.zero_address()),
        Eq(Gtxn[2].rekey_to(), Global.zero_address()),
        Eq(Gtxn[3].rekey_to(), Global.zero_address()),
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
def is_valid_user_optout():
    return And(
        Eq(Global.group_size(), Int(4)),
    )


@Subroutine(TealType.uint64)
def is_valid_creator_optout():
    return And(
        Eq(Gtxn[4].rekey_to(), Global.zero_address()),
        Eq(Global.group_size(), Int(5)),
        Eq(Gtxn[4].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[4].on_completion(), OnComplete.NoOp)
    )


@Subroutine(TealType.uint64)
def is_valid_base_optin():
    return And(
        Eq(Gtxn[0].rekey_to(), Global.zero_address()),
        Eq(Gtxn[1].rekey_to(), Global.zero_address()),
        Eq(Gtxn[2].rekey_to(), Global.zero_address()),
        Eq(Gtxn[3].rekey_to(), Global.zero_address()),
        Eq(Gtxn[4].rekey_to(), Global.zero_address()),
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
def is_valid_user_optin():
    return And(
        Eq(Global.group_size(), Int(5)),
    )


@Subroutine(TealType.uint64)
def is_valid_creator_optin():
    return And(
        Eq(Gtxn[5].rekey_to(), Global.zero_address()),
        Eq(Global.group_size(), Int(6)),
        Eq(Gtxn[5].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[5].on_completion(), OnComplete.NoOp)
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
# app arg: "dapp" dapp_name app_id
# acct arg: app_id
# global registry will have
# Key: dapp_name (max 10B)
# Value: app_id (8B) : dapp_idx (4B)
# App id is used to check if personal notification request comes from owner of app and
# also to fetch public notification for a dapp.
# Dapp_idx acts as dapp index aka replacement for dapp name for reference in personal msg box storage
# Stores MAX_MAIN_BOX_NUM_CHUNKS 26B key value pairs i.e., MAX_MAIN_BOX_NUM_CHUNKS dapps (MAX_MAIN_BOX_NUM_CHUNKS*26=32760)
# Stores dapp count in global state
# We don't check if dapp name is duplicate
#   1. what if someone claims the name prior to genuine party?
#   2. verify should solve this issue
@Subroutine(TealType.none)
def register_dapp():
    name = ScratchVar(TealType.bytes)

    return Seq(
        # dapp name
        name.store(dapp_name(Gtxn[1].application_args[1])),
        app_id_creator := AppParam.creator(Txn.applications[1]),
        Assert(
            And(
                Gtxn[1].application_args.length() == Int(3),
                Gtxn[1].applications.length() == Int(1),
                Gtxn[1].application_args[0] == TYPE_DAPP,
                # if app_id belongs to sender
                app_id_creator.hasValue(),
                Eq(
                    app_id_creator.value(),
                    Gtxn[1].sender(),
                ),
                # amt is >= optin fee
                Ge(Gtxn[0].amount(), Int(DAPP_OPTIN_FEE)),
            ),
        ),

        # ************* START *************
        # write message
        # this ranges from 0 to MAX_MAIN_BOX_NUM_CHUNKS
        (next_gstate_index := ScratchVar(TealType.bytes)).store(Itob(
            (Btoi(load_idx_gstate()) + Int(1)) % MAX_MAIN_BOX_NUM_CHUNKS
        )),
        # update index (position in box storage)
        set_idx_gstate(next_gstate_index.load()),
        (msg := ScratchVar(TealType.bytes)).store(
            Concat(
                # dapp name, app id, idx
                # TODO: This is a security risk app arg may be different from apps array
                name.load(), DELIMITER, Gtxn[1].application_args[2], DELIMITER,
                # we only use 4 bytes dapp index. The scratch slot is 8 bytes.
                # E.g. 1004 is stored as 00001004
                Extract(next_gstate_index.load(), Int(4), Int(4)), DELIMITER,
                # unverified
                Bytes("u")
            )
        ),
        write_to_box(NOTIBOY_BOX, next_gstate_index.load(), msg.load(), MAX_MAIN_BOX_MSG_SIZE, Int(0)),
        # write message
        # ************* END *************
        Approve()
    )


# invoked as part of dapp opt-in
# app arg: "dapp" dapp_name app_id
# acct arg: app_id
# 1. remove entry from global state
# 2. decrement dapp count
# TODO: 3. adjust index so that slot can be used (for reclaiming). A delete may happen in the middle of box. Reclamation can be a separate workflow
# Fetch all filled slots, write to box in maintenance mode i.e., when opt in is disabled
# MO: we check if app_id is owned by sender. If yes, we search box for dapp_name:app_id prefix and delete the entry
@Subroutine(TealType.none)
def deregister_dapp():
    name = ScratchVar(TealType.bytes)
    return Seq([

        app_id_creator := AppParam.creator(Txn.applications[1]),
        Assert(
            And(
                Gtxn[0].application_args.length() == Int(4),
                Gtxn[0].applications.length() == Int(1),
                Gtxn[0].application_args[0] == TYPE_DAPP,
                # if app_id belongs to sender
                app_id_creator.hasValue(),
                Eq(
                    app_id_creator.value(),
                    Txn.sender(),
                ),
            ),
        ),

        # dapp name
        name.store(dapp_name(Gtxn[0].application_args[1])),
        (prefix := ScratchVar(TealType.bytes)).store(
            Concat(
                # dapp name, app id
                # TODO: This is a security risk app arg may be different from apps array
                name.load(), DELIMITER, Gtxn[0].application_args[2], DELIMITER
            )
        ),
        Pop(prefix.load()),
        (start_idx := ScratchVar(TealType.uint64)).store(
            Mul(
                Btoi(Gtxn[0].application_args[3]),
                MAX_MAIN_BOX_MSG_SIZE
            )
        ),
        If(
            BytesEq(
                App.box_extract(NOTIBOY_BOX, start_idx.load(), Len(prefix.load())),
                prefix.load()
            )
        )
        .Then(
            App.box_replace(NOTIBOY_BOX, start_idx.load(),
                            Extract(ERASE_BYTES, Int(0), MAX_MAIN_BOX_MSG_SIZE)),
        )
        # compulsorily delete else Channel List will display non-existent channel
        .Else(Reject()),
    ])


# arg: "user"
@Subroutine(TealType.none)
def deregister_user():
    return Seq(
        Assert(App.box_delete(Gtxn[0].sender())),
        Approve()
    )


# invoked as part of user opt-in
# Creates a box with 32B user's public key as name
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


# initialise index to 0 for main box
@Subroutine(TealType.bytes)
def load_idx_gstate():
    return Seq([
        index_val := App.globalGetEx(app_id, INDEX_KEY),
        If(Not(index_val.hasValue()))
        .Then(App.globalPut(INDEX_KEY, Itob(Int(0)))),
        App.globalGet(INDEX_KEY)
    ])


# initialise index to 0
@Subroutine(TealType.none)
def set_idx_gstate(idx):
    return Seq([
        App.globalPut(INDEX_KEY, idx)
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
def write_to_box(box_name, start_idx, msg, msg_len, overwrite):
    return Seq(
        (start_byte := ScratchVar(TealType.uint64)).store(Mul(Btoi(start_idx), msg_len)),
        # if overwrite is disabled
        If(Eq(overwrite, Int(0)))
        .Then(
            Assert(
                Eq(
                    App.box_extract(box_name, start_byte.load(), msg_len),
                    Extract(ERASE_BYTES, Int(0), msg_len)
                )
            )
        ),
        App.box_replace(box_name, start_byte.load(), Extract(ERASE_BYTES, Int(0), msg_len)),
        App.box_replace(box_name, start_byte.load(), Extract(msg, Int(0), min_val(msg_len, Len(msg))))
    )


# to store list of dapps opted in by user
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
        (Btoi(load_idx_from_lstate(Txn.accounts[1])) + Int(1)) % MAX_USER_BOX_LEN
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
            Eq(Gtxn[1].application_args.length(), Int(3)),
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
            Eq(Gtxn[0].application_args.length(), Int(4)),
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