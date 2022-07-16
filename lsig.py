from pyteal import *

ADDR = "3"


def program(addr=ADDR):
    return BytesNeq(Bytes(addr), Bytes(""))


if __name__ == "__main__":
    print(compileTeal(program(), mode=Mode.Signature, version=6))
