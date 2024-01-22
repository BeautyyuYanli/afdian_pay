from typing import Any, Dict, Self

import msgspec


class StructSpec(msgspec.Struct):
    @classmethod
    def from_json(cls, buf: bytes) -> Self:
        return msgspec.json.decode(buf, type=cls)

    @classmethod
    def from_toml(cls, buf: bytes) -> Self:
        return msgspec.toml.decode(buf, type=cls)

    @classmethod
    def from_dict(cls, buf: Dict[str, Any]) -> Self:
        return msgspec.convert(buf, cls)

    @classmethod
    def from_any(cls, buf: Any) -> Self:
        return msgspec.convert(buf, cls, from_attributes=True)

    def to_json(self) -> bytes:
        return msgspec.json.encode(self)

    def to_toml(self) -> bytes:
        return msgspec.toml.encode(self)

    def to_dict(self) -> Dict[str, Any]:
        return msgspec.to_builtins(self)
