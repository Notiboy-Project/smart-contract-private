from pyteal import *

TESTNET = Bytes('testnet')
SANDBOX = Bytes('sandbox')
MAINNET = Bytes('mainnet')
# sandbox, testnet, mainnet
RUNNING_MODE = SANDBOX

TYPE_DAPP = Bytes("dapp")
TYPE_USER = Bytes("user")
NOTIBOY_BOX = Bytes("notiboy")
MSG_COUNT = Bytes("msgcount")
WHOAMI = Bytes("whoami")
INDEX_KEY = Bytes("index")
DELIMITER = Bytes(":")
DAPP_NAME_MAX_LEN = Int(10)
USDC_ASSET = Bytes("USDC")

# LSTATE
MAX_LSTATE_MSG_SIZE = Int(120)
MAX_LSTATE_SLOTS = Int(13)
LSTATE_INDEX_SLOT = Int(16)
LSTATE_COUNTER_SLOT = Int(16)

# USER BOX
MAX_USER_BOX_SIZE = Int(14336)
# include 8B ts, 8B app id, 280B data
MAX_USER_BOX_MSG_SIZE = Int(296)
MAX_USER_BOX_SLOTS = Div(MAX_USER_BOX_SIZE, MAX_USER_BOX_MSG_SIZE)

# MAIN BOX
MAX_MAIN_BOX_SIZE = Int(32768)
MAX_MAIN_BOX_MSG_SIZE = Int(23)
MAX_MAIN_BOX_SLOTS = Div(MAX_MAIN_BOX_SIZE, MAX_MAIN_BOX_MSG_SIZE)

# DAPP_NAME_MAX_LEN long
DAPP_NAME_PADDING = Bytes("::::::::::")
ERASE_BYTES = Bytes(
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")


@Subroutine(TealType.bytes)
def notiboy_address():
    return Seq(
        If(Eq(RUNNING_MODE, SANDBOX))
        .Then(
            Addr("EBM3V64MKXXIZ4ILJXLGJ6RDIOHXTSJ5HP7GD5MSPL2JWB34CIVE4JSOOE")
        )
        .Else(
            Addr("PMJ44TV52KSPIP6RMTPCEPXTFWKGCNQ2YDTYXQYDXU2OG7CMHZXEAN4W2E")
        )
    )


@Subroutine(TealType.uint64)
def dapp_optin_fee():
    return Seq(
        If(Eq(RUNNING_MODE, SANDBOX))
        .Then(
            # 1 Algo
            Int(1000000)
        )
        .Else(
            # 25 USDC
            Int(25000000)
        )
    )


@Subroutine(TealType.uint64)
def user_optin_fee():
    return Seq(
        If(Eq(RUNNING_MODE, SANDBOX))
        .Then(
            # 1 Algo
            Int(1000000)
        )
        .Else(
            # 5 algo
            Int(5000000)
        )
    )
