from sc.util import *


@Subroutine(TealType.uint64)
def is_pay_limit_reached():
    return Seq(
        (msgcount := ScratchVar(TealType.bytes)).store(
            Extract(App.localGet(Txn.sender(), MSG_COUNT), Int(0), Int(8))
        ),
        And(
            Eq(
                Mod(
                    Btoi(msgcount.load()),
                    PAYABLE_MSG_LIMIT
                ),
                Int(0)
            ),
            Ge(Btoi(msgcount.load()), Int(1))
        )
    )


@Subroutine(TealType.uint64)
def ensure_payment():
    return Seq(
        If(Eq(RUNNING_MODE, SANDBOX))
        .Then(
            And(
                Eq(Gtxn[0].type_enum(), TxnType.Payment),
                Eq(Gtxn[0].receiver(), notiboy_address()),
                # amt is >= msg limit fee
                Ge(Gtxn[0].amount(), msg_barrier_unblock_fee()),
            )
        )
        .Else(
            assetName := AssetParam.name(Txn.assets[0]),
            And(
                Eq(Gtxn[0].type_enum(), TxnType.AssetTransfer),
                Eq(Gtxn[0].asset_receiver(), notiboy_address()),
                Txn.assets.length() == Int(1),
                # amt is >= msg limit fee
                Ge(Gtxn[0].asset_amount(), msg_barrier_unblock_fee()),
                Eq(assetName.value(), USDC_ASSET),
            )
        )
    )


@Subroutine(TealType.uint64)
def is_pay_required():
    return Seq(
        If(is_pay_limit_reached())
        .Then(
            validate_rekeys(Int(0), Int(2)),
            And(
                Eq(Global.group_size(), Int(3)),
                ensure_payment(),
            )
        )
        .Else(
            validate_rekeys(Int(0), Int(1)),
            Eq(Global.group_size(), Int(2)),
        )
    )


@Subroutine(TealType.uint64)
def is_valid_private_notification():
    return Seq(
        validate_rekeys(Int(0), Int(0)),
        And(
            Eq(Global.group_size(), Int(1)),
            # rcvr opted in?
            App.optedIn(Txn.accounts[1], APP_ID),
            # rcvr opted in to creator's app?
            App.optedIn(Txn.accounts[1], Txn.applications[1]),
            # creator opted in?
            App.optedIn(Txn.sender(), APP_ID),
            # is rcvr address passed?
            Eq(Txn.accounts.length(), Int(1)),
            # "pvt_notify" dapp_name
            Eq(Txn.application_args.length(), Int(2)),
            # creator's channel id passed?
            Eq(Txn.applications.length(), Int(1)),
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
        App.optedIn(Txn.sender(), APP_ID),
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
        (whoami := ScratchVar(TealType.bytes)).store(App.localGet(Txn.sender(), WHOAMI)),
        Assert(
            And(
                # if whoami is not set, clearstate invoked to reset counter?
                Neq(whoami.load(), Bytes("")),
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
        inc_pub_msg_count(Txn.sender()),
        # write message
        App.localPut(Txn.sender(), next_lstate_index.load(), trim_string(Txn.note(), MAX_LSTATE_MSG_SIZE)),
    )


# app arg: "pvt_notify" dapp_name index_position
# apps: app_id
# acct arg: receiver_address
@Subroutine(TealType.none)
def send_personal_msg():
    return Seq(
        (whoami := ScratchVar(TealType.bytes)).store(App.localGet(Txn.sender(), WHOAMI)),
        app_id_creator := AppParam.creator(Txn.applications[1]),
        Assert(
            And(
                # if whoami is not set, clearstate invoked to reset counter?
                Neq(whoami.load(), Bytes("")),
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
        inc_pvt_msg_count(Txn.sender()),
        # increase 'received' msg count of rcvr
        inc_pvt_msg_count(Txn.accounts[1]),
        (data := ScratchVar(TealType.bytes)).store(
            Concat(
                Itob(Global.latest_timestamp()),
                Itob(Txn.applications[1]),
                Extract(Txn.note(), Int(0), min_val(Int(280), Len(Txn.note()))),
            )
        ),
        write_to_box(Txn.accounts[1], next_lstate_index.load(), data.load(), MAX_USER_BOX_MSG_SIZE, Int(1)),
    )
