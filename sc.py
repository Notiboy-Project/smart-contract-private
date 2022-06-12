from pyteal import *

is_creator = Assert(Txn.sender() == Global.creator_address())
app_id = Global.current_application_id()


handle_creation = Seq([
    App.globalPut(Bytes("Creator"), Bytes("Deepak")),
    Approve()
])

@Subroutine(TealType.uint64)
def is_creator():
    return Eq(Txn.sender(), Global.creator_address())


handle_optin = Seq([
    If(App.optedIn(Txn.sender(), app_id), Approve()),
    Approve()
])
# no txn should clear the local state
handle_closeout = Reject()
# txn can update the app only if initiated by creator
handle_updateapp = Return(is_creator())
# no txn should delete the app
handle_deleteapp = Return(is_creator())


index = ScratchVar(TealType.bytes)
next_index = ScratchVar(TealType.bytes)
index_val = App.globalGetEx(app_id, Bytes("index"))
init_index = Seq([
        index_val,
        If(Not(index_val.hasValue()))
        .Then(App.globalPut(Bytes("index"), Itob(Int(0)))),
        App.globalGet(Bytes("index"))
])

notify = Seq([
    index.store(init_index),
    next_index.store(Itob(
        (Btoi(index.load()) + Int(1)) % Int(16)
    )),
    If(Btoi(next_index.load()) == Int(0))
    .Then(next_index.store(Itob(Int(1)))),
    # App.localDel(Txn.sender(), Itob(Int(16))),
    App.localDel(Txn.accounts[0], next_index.load()),
    App.localPut(Txn.sender(), next_index.load(), Txn.tx_id()),
    App.globalPut(Bytes("index"), next_index.load()),
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