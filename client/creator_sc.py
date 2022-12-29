from pyteal import *


def approval_program():
    program = Approve()

    return compileTeal(program, Mode.Application, version=8)


def clear_state_program():
    program = Approve()
    return compileTeal(program, Mode.Application, version=8)
