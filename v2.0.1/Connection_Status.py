from enum import Enum
class Connection_Status(Enum):
    PENDING = 1
    CONNECTED = 2
    VIDEO_ERROR = 3
    SOCKET_TIMEOUT = 4
    CONNECTION_ABORTED = 5