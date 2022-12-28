from sc.util import *


@Subroutine(TealType.uint64)
def is_valid_private_notification():
    return Seq(
        validate_noops(Int(0), Int(1)),
        validate_rekeys(Int(0), Int(1)),
        And(
            # rcvr opted in?
            App.optedIn(Txn.accounts[1], app_id),
            # rcvr opted in to creator's app?
            App.optedIn(Txn.accounts[1], Txn.applications[1]),
            # creator opted in?
            App.optedIn(Txn.sender(), app_id),
            # is rcvr address passed?
            Eq(Txn.accounts.length(), Int(1)),
            # "pvt_notify" dapp_name index_position
            Eq(Txn.application_args.length(), Int(3)),
            # creator's channel id passed?
            Eq(Txn.applications.length(), Int(1)),
            Eq(Global.group_size(), Int(2)),
        )
    )


@Subroutine(TealType.uint64)
def is_valid_public_notification():
    return And(
        # should contain just 1 txn
        Eq(Global.group_size(), Int(1)),
        Eq(Txn.application_args.length(), Int(1)),
        Eq(Txn.applications.length(), Int(1)),
        Eq(Txn.rekey_to(), Global.zero_address()),
        Eq(Txn.type_enum(), TxnType.ApplicationCall),
        Eq(Txn.on_completion(), OnComplete.NoOp),
        # creator opted in?
        App.optedIn(Txn.sender(), app_id),
    )


# app arg: "pub_notify" dapp_name app_id index_position
# acct arg: app_id
# We don't have to care even if user impersonates a creator because all the writes to local state of user goes in vain
# as we display local states of only channels listed in main box.
# Checking this requires extra 4 txns for box read budget
@Subroutine(TealType.none)
def send_public_msg():
    return Seq(
        app_id_creator := AppParam.creator(Txn.applications[1]),
        Assert(
            And(
                # if app_id belongs to sender
                app_id_creator.hasValue(),
                Eq(
                    app_id_creator.value(),
                    Txn.sender(),
                ),
            ),
        ),
        # ranges from 0 to 15, but we don't 0th location as we store this index there
        (next_lstate_index := ScratchVar(TealType.bytes)).store(Itob(
            (Btoi(load_idx_from_lstate(Txn.sender())) + Int(1)) % MAX_LSTATE_SLOTS
        )),
        App.localDel(Txn.sender(), next_lstate_index.load()),
        # set index key
        App.localPut(Txn.sender(), INDEX_KEY, next_lstate_index.load()),
        # increment msg count
        inc_msg_count(Txn.sender()),
        # write message
        App.localPut(Txn.sender(), next_lstate_index.load(), trim_string(Txn.note(), MAX_LSTATE_MSG_SIZE)),
    )


# app arg: "pvt_notify" dapp_name index_position
# apps: app_id
# acct arg: receiver_address
@Subroutine(TealType.none)
def send_personal_msg():
    return Seq(
        app_id_creator := AppParam.creator(Txn.applications[1]),
        Assert(
            And(
                # if app_id belongs to sender
                app_id_creator.hasValue(),
                Eq(
                    app_id_creator.value(),
                    Txn.sender(),
                ),
            ),
        ),
        # this ranges from 0 to MAX_USER_BOX_SLOTS
        (next_lstate_index := ScratchVar(TealType.bytes)).store(Itob(
            (Btoi(load_idx_from_lstate(Txn.accounts[1])) + Int(1)) % MAX_USER_BOX_SLOTS
        )),
        # update index key in receiver's local state
        App.localPut(Txn.accounts[1], INDEX_KEY, next_lstate_index.load()),
        # increase 'sent' msg count of dapp
        inc_msg_count(Txn.sender()),
        # increase 'received' msg count of rcvr
        inc_msg_count(Txn.accounts[1]),
        (data := ScratchVar(TealType.bytes)).store(
            Concat(
                Itob(Global.latest_timestamp()),
                Itob(Txn.applications[1]),
                Extract(Txn.note(), Int(0), min_val(Int(280), Len(Txn.note()))),
            )
        ),
        write_to_box(Txn.accounts[1], next_lstate_index.load(), data.load(), MAX_USER_BOX_MSG_SIZE, Int(1)),
    )
