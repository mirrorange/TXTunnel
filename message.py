import base64
import json
from enum import Enum


class MessageType(Enum):
    NEW_CONNECTION = "NEW"
    CLOSE_CONNECTION = "CLOSE"
    DATA = "DATA"


class Message:
    target: str
    conn_id: str
    type: MessageType
    data: bytes

    def __init__(self, target: str, conn_id: str, type: MessageType, data: bytes):
        self.target = target
        self.conn_id = conn_id
        self.type = type
        self.data = data

    def __str__(self):
        return (
            json.dumps(
                {
                    "target": self.target,
                    "conn_id": self.conn_id,
                    "type": self.type.value,
                    "data": base64.b64encode(self.data).decode(),
                },
                separators=(",", ":"),
            )
            + "\r\n"
        )

    @staticmethod
    def create(target: str, conn_id: str, type: MessageType, data: bytes) -> "Message":
        return Message(
            target=target,
            conn_id=conn_id,
            type=type,
            data=data,
        )

    @staticmethod
    def from_str(s: str) -> "Message":
        try:
            obj = json.loads(s)
            return Message(
                target=obj["target"],
                conn_id=obj["conn_id"],
                type=MessageType(obj["type"]),
                data=base64.b64decode(obj["data"]),
            )
        except:
            return None
