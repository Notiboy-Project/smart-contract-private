from sc.util import *

'''
app_args: verify dapp_name index_position
apps: app_id
'''


@Subroutine(TealType.uint64)
def is_channel_valid_for_verification():
    return Seq(
        # dapp name
        (name := ScratchVar(TealType.bytes)).store(sanitize_dapp_name(Txn.application_args[1], DAPP_NAME_MAX_LEN)),
        (start_idx := ScratchVar(TealType.uint64)).store(
            Mul(
                Btoi(Txn.application_args[2]),
                MAX_MAIN_BOX_MSG_SIZE
            )
        ),
        app_id_creator := AppParam.creator(Txn.applications[1]),
        And(
            Eq(Txn.application_args.length(), Int(3)),
            # is app id passed?
            Eq(Txn.applications.length(), Int(1)),
            # if app_id creator opted in?
            App.optedIn(app_id_creator.value(), APP_ID),
            # called by creator?
            is_creator(),
            is_creator_onboarded(name.load(), start_idx.load(), Itob(Txn.applications[1])),
        )
    )


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


'''
app_args: verify dapp_name index_position
apps: app_id
'''


@Subroutine(TealType.uint64)
def mark_channel_verified():
    return Seq([
        # dapp name
        (name := ScratchVar(TealType.bytes)).store(sanitize_dapp_name(Txn.application_args[1], DAPP_NAME_MAX_LEN)),
        (start_idx := ScratchVar(TealType.uint64)).store(
            Mul(
                Btoi(Txn.application_args[2]),
                MAX_MAIN_BOX_MSG_SIZE
            )
        ),
        (msg := ScratchVar(TealType.bytes)).store(
            Concat(
                # dapp name, app id, idx
                name.load(), Itob(Txn.applications[1]),
                # we only use 4 bytes dapp index. The scratch slot is 8 bytes.
                # E.g. 1004 is stored as 00001004
                Extract(Itob(start_idx.load()), Int(4), Int(4)),
                # mark verified
                Bytes("v")
            )
        ),
        write_to_box(NOTIBOY_BOX, start_idx.load(), msg.load(), MAX_MAIN_BOX_MSG_SIZE, Int(0)),
        Approve()
    ])
