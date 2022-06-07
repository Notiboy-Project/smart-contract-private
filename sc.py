from pyteal import *


handle_creation = Seq([
    App.globalPut(Bytes("Creator"), Bytes("Deepak")),
    Approve()
])

is_creator = Assert(Txn.sender() == Global.creator_address())


@Subroutine(TealType.uint64)
def is_creator():
    return Eq(Txn.sender(), Global.creator_address())


handle_optin = Seq([
    If(App.optedIn(Txn.sender(), Global.current_application_id()), Approve()),
    Approve()
])
# no txn should clear the local state
handle_closeout = Reject()
# txn can update the app only if initiated by creator
handle_updateapp = Return(is_creator())
# no txn should delete the app
handle_deleteapp = Return(is_creator())

notify = Seq([
    App.localPut(Txn.accounts[0], Bytes("TxnID"), Txn.tx_id()),
    Approve()
])

# deduct = Seq([
#     If(App.globalGet(Bytes("Count")) > Int(0))
#     .Then(App.globalPut(Bytes("Count"), App.globalGet(Bytes("Count"))-Int(1))),
#     Approve()
# ])

# application calls
handle_noop = Seq([
        Cond(
        [Txn.application_args[0] == Bytes("Notify"), notify]
    )
])


def approval_program():
    program = Cond(
        [Txn.application_id() == Int(0), handle_creation],
        [Txn.on_completion() == OnComplete.OptIn, handle_optin],
        [Txn.on_completion() == OnComplete.CloseOut, handle_closeout],
        [Txn.on_completion() == OnComplete.UpdateApplication, handle_updateapp],
        [Txn.on_completion() == OnComplete.DeleteApplication, handle_deleteapp],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop]
    )

    return compileTeal(program, Mode.Application, version=6)

def clear_state_program():
    program = Return(Int(1))
    return compileTeal(program, Mode.Application, version=6)

print(approval_program())
print(clear_state_program())