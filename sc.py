from pyteal import *


handle_creation = Seq(
    App.globalPut(Bytes("Count"), Int(0)),
    Return(Int(1))
)

handle_optin = Return(Int(1))
# no txn should clear the local state
handle_closeout = Return(Int(0))
# no txn should update the app
handle_updateapp = Return(Int(0))
# no txn should delete the app
handle_deleteapp = Return(Int(0))
# these are typically calls to the app
handle_noop = Return(Int(0))

add = Seq(
    App.globalPut(Bytes("Count"), App.globalGet(Bytes("Count"))+Int(1)),
    Return(Int(1))
)
deduct = Seq(
    If(App.globalGet(Bytes("Count")) > Int(0),
        App.globalPut(Bytes("Count"), App.globalGet(Bytes("Count"))-Int(1)),
       ),
    Return(Int(1))
)

handle_noop = Seq(
    # First, lets fail immediately if this transaction is grouped with any others
    Assert(Global.group_size() == Int(1)),
    Cond(
        [Txn.application_args[0] == Bytes("Add"), add],
        [Txn.application_args[0] == Bytes("Deduct"), deduct]
    )
)


def approval_program():
    program = Cond(
        [Txn.application_id() == Int(0), handle_creation],
        [Txn.on_completion() == OnComplete.OptIn, handle_optin],
        [Txn.on_completion() == OnComplete.CloseOut, handle_closeout],
        [Txn.on_completion() == OnComplete.UpdateApplication, handle_updateapp],
        [Txn.on_completion() == OnComplete.DeleteApplication, handle_deleteapp],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop]
    )

    return compileTeal(program, Mode.Application, version=5)

def clear_state_program():
    program = Return(Int(1))
    return compileTeal(program, Mode.Application, version=5)

print(approval_program())
print(clear_state_program())