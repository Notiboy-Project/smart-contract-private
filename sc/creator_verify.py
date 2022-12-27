from sc.util import *


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


@Subroutine(TealType.uint64)
def verify_dapp_addr():
    val = App.globalGet(Txn.application_args[1])
    return Seq([
        Assert(
            And(
                Ge(Len(val), Int(65)),
                Eq(
                    Extract(val, Int(33), Int(32)), Txn.accounts[1]
                )
            )
        ),
        Approve()
    ])


@Subroutine(TealType.uint64)
def mark_dapp_verified():
    val = ScratchVar(TealType.bytes)
    return Seq([
        val.store(App.globalGet(Txn.application_args[1])),
        If(Not(is_verified()))
        .Then(
            Seq([
                App.globalDel(Txn.application_args[1]),
                App.globalPut(Txn.application_args[1],
                              Concat(
                                  val.load(), Bytes(":v"),
                              )
                              ),
                Approve()
            ])
        ),
        Approve()
    ])
