from sc.util import *

'''
app_args: verify dapp_name index_position
apps: app_id
'''


@Subroutine(TealType.uint64)
def is_channel_valid_for_verification():
    return Seq(
        validate_rekeys(Int(0), Int(4)),
        validate_noops(Int(0), Int(4)),
        # dapp name
        (name := ScratchVar(TealType.bytes)).store(sanitize_dapp_name(Txn.application_args[1], DAPP_NAME_MAX_LEN)),
        (start_idx := ScratchVar(TealType.uint64)).store(
            Mul(
                Btoi(Txn.application_args[2]),
                MAX_MAIN_BOX_MSG_SIZE
            )
        ),
        And(
            Eq(Global.group_size(), Int(5)),
            Eq(Txn.application_args.length(), Int(3)),
            # is app id passed?
            Eq(Txn.applications.length(), Int(1)),
            # called by creator?
            is_creator(),
            is_creator_onboarded(name.load(), start_idx.load(), Itob(Txn.applications[1])),
        )
    )


'''
app_args: verify dapp_name index_position
apps: app_id
'''


@Subroutine(TealType.uint64)
def set_verify_bit(value):
    return Seq([
        # dapp name
        (name := ScratchVar(TealType.bytes)).store(sanitize_dapp_name(Txn.application_args[1], DAPP_NAME_MAX_LEN)),
        (msg := ScratchVar(TealType.bytes)).store(
            Concat(
                # dapp name, app id, idx
                name.load(), Itob(Txn.applications[1]),
                # we only use 4 bytes dapp index. The scratch slot is 8 bytes.
                # E.g. 1004 is stored as 00001004
                Extract(Txn.application_args[2], Int(4), Int(4)),
                # set verified bit
                value
            )
        ),
        write_to_box(NOTIBOY_BOX, Txn.application_args[2], msg.load(), MAX_MAIN_BOX_MSG_SIZE, Int(1)),
        Approve()
    ])


@Subroutine(TealType.uint64)
def mark_channel_verified():
    return set_verify_bit(Bytes("v"))


@Subroutine(TealType.uint64)
def mark_channel_unverified():
    return set_verify_bit(Bytes("u"))
