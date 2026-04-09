from google.api import annotations_pb2 as _annotations_pb2
from protoc_gen_openapiv2.options import annotations_pb2 as _annotations_pb2_1
import permission_pb2 as _permission_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class JoinRequest(_message.Message):
    __slots__ = ("namespace", "player_id")
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
    namespace: str
    player_id: str
    def __init__(self, namespace: _Optional[str] = ..., player_id: _Optional[str] = ...) -> None: ...

class JoinResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CheckRequest(_message.Message):
    __slots__ = ("namespace", "player_id")
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
    namespace: str
    player_id: str
    def __init__(self, namespace: _Optional[str] = ..., player_id: _Optional[str] = ...) -> None: ...

class CheckResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...
