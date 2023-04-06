from sc.util import *

'''
app arg: update_box index dapp_name new_dapp_name
apps: app_id
acct: creator addr
'''


# Layout: dapp_name (max 10B) + app_id (8B) + verified (1B)
# MO: we check if app_id is owned by creator. If yes, we search box for dapp_name:app_id prefix and replace the entry
@Subroutine(TealType.uint64)
def edit_box():
    name = ScratchVar(TealType.bytes)
    new_name = ScratchVar(TealType.bytes)

    return Seq(
        app_id_creator := AppParam.creator(Txn.applications[1]),
        Assert(
            And(
                Txn.application_args.length() == Int(4),
                Txn.applications.length() == Int(1),
                Txn.accounts.length() == Int(1),
                # if app_id belongs to sender
                app_id_creator.hasValue(),
                Eq(
                    app_id_creator.value(),
                    Txn.accounts[1],
                ),
            ),
        ),

        # ************* START *************
        # dapp name
        name.store(sanitize_dapp_name(Txn.application_args[2], DAPP_NAME_MAX_LEN)),
        new_name.store(sanitize_dapp_name(Txn.application_args[3], DAPP_NAME_MAX_LEN)),
        (start_idx := ScratchVar(TealType.uint64)).store(
            Mul(
                Btoi(Txn.application_args[1]),
                MAX_MAIN_BOX_MSG_SIZE
            )
        ),
        If(is_creator_onboarded(name.load(), start_idx.load(), Itob(Txn.applications[1])))
        .Then(
            (msg := ScratchVar(TealType.bytes)).store(
                Concat(
                    # dapp name, app id
                    new_name.load(), Itob(Txn.applications[1]),
                    # verified bit
                    Extract(extract_from_main_box(start_idx.load()), Int(18), Int(1))
                )
            ),
            App.localPut(Txn.accounts[1], WHOAMI, msg.load()),
            write_to_box(NOTIBOY_BOX, Txn.application_args[1], msg.load(), MAX_MAIN_BOX_MSG_SIZE, Int(1)),
        ),
        # ************* END *************
        Approve()
    )
