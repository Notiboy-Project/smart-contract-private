from pyteal import *

TYPE_DAPP = Bytes("dapp")
TYPE_USER = Bytes("user")
NOTIBOY_BOX = Bytes("notiboy")
MSG_COUNT = Bytes("msgcount")
INDEX_KEY = Bytes("index")
DELIMITER = Bytes(":")
DAPP_NAME_MAX_LEN = Int(10)
MAX_BOX_SIZE = Int(32768)
MAX_LSTATE_SLOTS = Int(14)
LSTATE_INDEX_SLOT = Int(16)
LSTATE_COUNTER_SLOT = Int(16)
MAX_USER_BOX_SLOTS = Int(32)
MAX_MAIN_BOX_MSG_SIZE = Int(23)
MAX_USER_BOX_MSG_SIZE = Int(1024)
MAX_LSTATE_MSG_SIZE = Int(120)
MAX_MAIN_BOX_NUM_CHUNKS = Div(MAX_BOX_SIZE, MAX_MAIN_BOX_MSG_SIZE)

# dummy address that belongs to algo dispenser source account
NOTIBOY_ADDR = "3KOQUDTQAYKMXFL66Q5DS27FJJS6O3E2J3YMOC3WJRWNWJW3J4Q65POKPI"
# DAPP_NAME_MAX_LEN long
DAPP_NAME_PADDING = Bytes("::::::::::")
ERASE_BYTES = Bytes(
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# 1 algo
DAPP_OPTIN_FEE = 1000000
# 1 algo
USER_OPTIN_FEE = 1000000
