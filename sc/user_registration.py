from sc.util import *


@Subroutine(TealType.uint64)
def is_valid_user_optin():
    return Seq(
        validate_rekeys(Int(0), Int(1)),
        And(
            Eq(Global.group_size(), Int(2)),
            Eq(Gtxn[0].type_enum(), TxnType.Payment),
            Eq(Gtxn[0].receiver(), notiboy_address()),
        )
    )


@Subroutine(TealType.uint64)
def is_valid_user_optout():
    return Seq(
        validate_rekeys(Int(0), Int(0)),
        Eq(Global.group_size(), Int(1)),
    )


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
                Ge(Gtxn[0].amount(), user_optin_fee())
            )
        ),
        # create box with name as sender's 32B address
        Assert(App.box_create(Gtxn[0].sender(), MAX_USER_BOX_SIZE)),
        App.localPut(Txn.sender(), MSG_COUNT, Concat(Itob(Int(0)), DELIMITER, Itob(Int(0)))),
        App.localPut(Txn.sender(), INDEX_KEY, Itob(Int(0))),
        Approve()
    ])
