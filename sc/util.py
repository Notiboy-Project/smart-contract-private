from sc.constants import *

APP_ID = Global.current_application_id()


@Subroutine(TealType.uint64)
def is_creator_onboarded(name, start_idx, app_id):
    return Seq(
        (prefix := ScratchVar(TealType.bytes)).store(
            Concat(
                # dapp name, app id
                name, app_id,
            )
        ),
        Pop(prefix.load()),
        BytesEq(
            App.box_extract(NOTIBOY_BOX, start_idx, Len(prefix.load())),
            prefix.load()
        )
    )


@Subroutine(TealType.bytes)
# expects uint64 arg
def extract_from_main_box(start_idx):
    return Seq(
        App.box_extract(NOTIBOY_BOX, start_idx, MAX_MAIN_BOX_MSG_SIZE)
    )


@Subroutine(TealType.uint64)
def is_admin():
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
        Eq(Gtxn[0].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[0].on_completion(), OnComplete.CloseOut),
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
    return And(
        Eq(Gtxn[1].type_enum(), TxnType.ApplicationCall),
        Eq(Gtxn[1].on_completion(), OnComplete.OptIn),
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
        index_val := App.localGetEx(addr, APP_ID, INDEX_KEY),
        If(Not(index_val.hasValue()))
        .Then(App.localPut(addr, INDEX_KEY, Itob(Int(0)))),
        App.localGet(addr, INDEX_KEY)
    ])


# initialise index to 0 for main box
@Subroutine(TealType.bytes)
def load_idx_gstate():
    return Seq([
        index_val := App.globalGetEx(APP_ID, INDEX_KEY),
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
def update_lstate_msg_count(addr, pvt_count, pub_count):
    return Seq([
        count_val := App.localGetEx(addr, APP_ID, MSG_COUNT),
        If(Not(count_val.hasValue()))
        .Then(App.localPut(addr, MSG_COUNT,
                           # pvt count, public count
                           Concat(Itob(Int(0)), DELIMITER, Itob(Int(0))))
              ),
        (pvt := ScratchVar(TealType.bytes)).store(
            Extract(App.localGet(addr, MSG_COUNT), Int(0), Int(8))
        ),
        (pub := ScratchVar(TealType.bytes)).store(
            Extract(App.localGet(addr, MSG_COUNT), Int(9), Int(8))
        ),
        App.localPut(addr, MSG_COUNT,
                     Concat(
                         Itob(
                             Add(
                                 Btoi(pvt.load()), pvt_count
                             )
                         ),
                         DELIMITER,
                         Itob(
                             Add(
                                 Btoi(pub.load()), pub_count
                             )
                         )
                     )
                     )
    ])


@Subroutine(TealType.none)
def inc_pvt_msg_count(addr):
    return Seq([
        update_lstate_msg_count(addr, Int(1), Int(0))
    ])


@Subroutine(TealType.none)
def inc_pub_msg_count(addr):
    return Seq([
        update_lstate_msg_count(addr, Int(0), Int(1))
    ])


@Subroutine(TealType.none)
def update_global_msg_count(pvt_count, pub_count):
    return Seq([
        count_val := App.globalGetEx(APP_ID, MSG_COUNT),
        If(
            Or(
                Not(count_val.hasValue()),
                Lt(Len(count_val.value()), Int(17))
            )
        )
        .Then(App.globalPut(MSG_COUNT,
                            # pvt count, public count
                            Concat(Itob(Int(0)), DELIMITER, Itob(Int(0))))
              ),
        (pvt := ScratchVar(TealType.bytes)).store(
            Extract(App.globalGet(MSG_COUNT), Int(0), Int(8))
        ),
        (pub := ScratchVar(TealType.bytes)).store(
            Extract(App.globalGet(MSG_COUNT), Int(9), Int(8))
        ),
        App.globalPut(MSG_COUNT,
                      Concat(
                          Itob(
                              Add(
                                  Btoi(pvt.load()), pvt_count
                              )
                          ), DELIMITER,
                          Itob(
                              Add(
                                  Btoi(pub.load()), pub_count
                              )
                          )
                      )
                      )
    ])


@Subroutine(TealType.none)
def inc_global_pvt_msg_count():
    return Seq([
        update_global_msg_count(Int(1), Int(0))
    ])


@Subroutine(TealType.none)
def inc_global_pub_msg_count():
    return Seq([
        update_global_msg_count(Int(0), Int(1))
    ])


@Subroutine(TealType.none)
def update_global_optin_count(creator_count, user_count, op):
    return Seq([
        count_val := App.globalGetEx(APP_ID, OPTIN_COUNT),
        If(Not(count_val.hasValue()))
        .Then(App.globalPut(OPTIN_COUNT,
                            # creator count, user count
                            Concat(Itob(Int(2)), DELIMITER, Itob(Int(142))))
              ),
        (creator := ScratchVar(TealType.bytes)).store(
            Extract(App.globalGet(OPTIN_COUNT), Int(0), Int(8))
        ),
        (user := ScratchVar(TealType.bytes)).store(
            Extract(App.globalGet(OPTIN_COUNT), Int(9), Int(8))
        ),
        If(Eq(op, Bytes("add")))
        .Then(
            App.globalPut(OPTIN_COUNT,
                          Concat(
                              Itob(
                                  Add(
                                      Btoi(creator.load()), creator_count
                                  )
                              ), DELIMITER,
                              Itob(
                                  Add(
                                      Btoi(user.load()), user_count
                                  )
                              )
                          )
                          )
        )
        .Else(
            App.globalPut(OPTIN_COUNT,
                          Concat(
                              Itob(
                                  Minus(
                                      Btoi(creator.load()), creator_count
                                  )
                              ), DELIMITER,
                              Itob(
                                  Minus(
                                      Btoi(user.load()), user_count
                                  )
                              )
                          )
                          )
        )

    ])


@Subroutine(TealType.none)
def inc_global_user_count():
    return Seq([
        update_global_optin_count(Int(0), Int(1), Bytes("add"))
    ])


@Subroutine(TealType.none)
def inc_global_creator_count():
    return Seq([
        update_global_optin_count(Int(1), Int(0), Bytes("add"))
    ])


@Subroutine(TealType.none)
def dec_global_user_count():
    return Seq([
        update_global_optin_count(Int(0), Int(1), Bytes("minus"))
    ])


@Subroutine(TealType.none)
def dec_global_creator_count():
    return Seq([
        update_global_optin_count(Int(1), Int(0), Bytes("minus"))
    ])


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
