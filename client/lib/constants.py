NOTIBOY_ADDR = "EBM3V64MKXXIZ4ILJXLGJ6RDIOHXTSJ5HP7GD5MSPL2JWB34CIVE4JSOOE"
DAPP_NAME = "dapp1"
APP_ID = 114
CREATOR_APP_ID = 3
MAIN_BOX = "notiboy"
DAPP_NAME_MAX_LEN = 10
MAX_BOX_SIZE = 32768
MAX_LSTATE_SIZE = 16
MAX_USER_BOX_LEN = 32
MAX_MAIN_BOX_MSG_SIZE = 19
MAX_USER_BOX_MSG_SIZE = 296
MAX_MAIN_BOX_NUM_CHUNKS = MAX_BOX_SIZE / MAX_MAIN_BOX_MSG_SIZE
ASA_ASSET = 10458941
# sandbox, testnet, mainnet
RUNNING_MODE = 'sandbox'

if RUNNING_MODE == "testnet":
    APP_ID = 151040046
    NOTIBOY_ADDR = "PMJ44TV52KSPIP6RMTPCEPXTFWKGCNQ2YDTYXQYDXU2OG7CMHZXEAN4W2E"
    CREATOR_APP_ID = 151056581
