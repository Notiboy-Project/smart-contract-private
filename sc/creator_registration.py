from sc.util import *


@Subroutine(TealType.uint64)
def is_valid_creator_optout():
    return Seq(
        validate_rekeys(Int(0), Int(4)),
        validate_noops(Int(1), Int(4)),
        Eq(Global.group_size(), Int(5)),
    )


@Subroutine(TealType.uint64)
def is_valid_creator_optin():
    return Seq(
        validate_rekeys(Int(0), Int(5)),
        validate_noops(Int(2), Int(5)),
        Eq(Global.group_size(), Int(6))
    )


# invoked as part of dapp opt-in
# app arg: "dapp" dapp_name
# apps: app_id
# global registry will have
# Key: dapp_name (max 10B)
# Value: app_id (8B)  dapp_idx (4B) verified (1B)
# App id is used to check if personal notification request comes from owner of app and
# also to fetch public notification for a dapp.
# Dapp_idx acts as dapp index aka replacement for dapp name for reference in personal msg box storage
# Stores MAX_MAIN_BOX_NUM_CHUNKS 23B key value pairs i.e., MAX_MAIN_BOX_NUM_CHUNKS dapps (MAX_MAIN_BOX_NUM_CHUNKS*23=32760)
# Stores dapp count in global state
# We don't check if dapp name is duplicate
#   1. what if someone claims the name prior to genuine party?
#   2. verify should solve this issue
@Subroutine(TealType.none)
def register_dapp():
    name = ScratchVar(TealType.bytes)

    return Seq(
        # dapp name
        name.store(sanitize_dapp_name(Txn.application_args[1], DAPP_NAME_MAX_LEN)),
        app_id_creator := AppParam.creator(Txn.applications[1]),
        Assert(
            And(
                Txn.application_args.length() == Int(2),
                Txn.applications.length() == Int(1),
                Txn.application_args[0] == TYPE_DAPP,
                # if app_id belongs to sender
                app_id_creator.hasValue(),
                Eq(
                    app_id_creator.value(),
                    Txn.sender(),
                ),
                # # amt is >= optin fee
                Ge(Gtxn[0].amount(), Int(DAPP_OPTIN_FEE)),
            ),
        ),

        # ************* START *************
        # write message
        # this ranges from 0 to MAX_MAIN_BOX_NUM_CHUNKS
        (next_gstate_index := ScratchVar(TealType.bytes)).store(Itob(
            (Btoi(load_idx_gstate()) + Int(1)) % MAX_MAIN_BOX_SLOTS
        )),
        # update index (position in box storage)
        set_idx_gstate(next_gstate_index.load()),
        (msg := ScratchVar(TealType.bytes)).store(
            Concat(
                # dapp name, app id, idx
                name.load(), Itob(Txn.applications[1]),
                # we only use 4 bytes dapp index. The scratch slot is 8 bytes.
                # E.g. 1004 is stored as 00001004
                Extract(next_gstate_index.load(), Int(4), Int(4)),
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
# app arg: "dapp" dapp_name index_position
# apps: app_id
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
                Txn.application_args.length() == Int(3),
                Txn.applications.length() == Int(1),
                Txn.application_args[0] == TYPE_DAPP,
                # if app_id belongs to sender
                app_id_creator.hasValue(),
                Eq(
                    app_id_creator.value(),
                    Txn.sender(),
                ),
            ),
        ),
        # dapp name
        name.store(sanitize_dapp_name(Txn.application_args[1], DAPP_NAME_MAX_LEN)),
        (start_idx := ScratchVar(TealType.uint64)).store(
            Mul(
                Btoi(Txn.application_args[2]),
                MAX_MAIN_BOX_MSG_SIZE
            )
        ),
        If(is_creator_onboarded(name.load(), start_idx.load(), Itob(Txn.applications[1])))
        .Then(
            App.box_replace(NOTIBOY_BOX, start_idx.load(),
                            Extract(ERASE_BYTES, Int(0), MAX_MAIN_BOX_MSG_SIZE)),
        )
        # compulsorily delete else Channel List will display non-existent channel
        .Else(Reject()),
    ])
