from sc.constants import *

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
    return Seq(
        validate_rekeys(Int(0), Int(3)),
        validate_noops(Int(1), Int(3)),
        And(
            Eq(Gtxn[0].type_enum(), TxnType.ApplicationCall),
            Eq(Gtxn[0].on_completion(), OnComplete.CloseOut),
        )
    )


@Subroutine(TealType.none)
def validate_rekeys(i, j):
    return Seq(
        For((start_idx := ScratchVar(TealType.uint64)).store(i),
            start_idx.load() <= j,
            start_idx.store(start_idx.load() + Int(1))
            ).Do(
            Assert(
                Eq(
                    Gtxn[start_idx.load()].rekey_to(), Global.zero_address()
                )
            )
        )
    )


@Subroutine(TealType.none)
def validate_noops(i, j):
    return Seq(
        For((start_idx := ScratchVar(TealType.uint64)).store(i),
            start_idx.load() <= j,
            start_idx.store(start_idx.load() + Int(1))
            ).Do(
            Assert(
                And(
                    Eq(Gtxn[i].type_enum(), TxnType.ApplicationCall),
                    Eq(Gtxn[i].on_completion(), OnComplete.NoOp),
                )
            )
        )
    )


@Subroutine(TealType.uint64)
def is_valid_base_optin():
    return Seq(
        validate_rekeys(Int(0), Int(4)),
        validate_noops(Int(2), Int(4)),
        And(
            Eq(Gtxn[0].type_enum(), TxnType.Payment),
            Eq(Gtxn[0].receiver(), Addr(NOTIBOY_ADDR)),
            Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
            Eq(Gtxn[1].on_completion(), OnComplete.OptIn),
        )
    )


@Subroutine(TealType.bytes)
def sanitize_dapp_name(name, max_size):
    return Seq(
        (dapp_name := ScratchVar(TealType.bytes)).store(trim_string(name, max_size)),
        If(Len(dapp_name.load()) < DAPP_NAME_MAX_LEN)
        .Then(
            dapp_name.store(Concat(
                Extract(DAPP_NAME_PADDING, Int(0), (DAPP_NAME_MAX_LEN - Len(dapp_name.load()))),
                dapp_name.load()
            ))
        ),
        dapp_name.load()
    )


@Subroutine(TealType.bytes)
def trim_string(name, max_size):
    return (
        If(
            Len(name) > max_size
        )
        .Then(
            Extract(name, Int(0), max_size)
        )
        .Else(name)
    )


# initialise index to 0
@Subroutine(TealType.bytes)
def load_idx_from_lstate(addr):
    return Seq([
        index_val := App.localGetEx(addr, app_id, INDEX_KEY),
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
def write_to_box(box_name, start_idx, msg, max_msg_len, overwrite):
    return Seq(
        (start_byte := ScratchVar(TealType.uint64)).store(Mul(Btoi(start_idx), max_msg_len)),
        # if overwrite is disabled
        If(Eq(overwrite, Int(0)))
        .Then(
            Assert(
                Eq(
                    App.box_extract(box_name, start_byte.load(), max_msg_len),
                    Extract(ERASE_BYTES, Int(0), max_msg_len)
                )
            )
        ),
        App.box_replace(box_name, start_byte.load(), Extract(ERASE_BYTES, Int(0), max_msg_len)),
        App.box_replace(box_name, start_byte.load(), Extract(msg, Int(0), min_val(max_msg_len, Len(msg))))
    )