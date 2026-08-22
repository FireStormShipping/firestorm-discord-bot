from abc import ABC
from typing import Any

from .app_types import DatasetEntry


class Encoder(ABC):
    def encode(self, obj: object) -> Any:
        """Encode into the Encoder format."""
        raise NotImplementedError

    def decode(self, string: str, to_type: str) -> Any:
        """Decode from the Encoder format."""
        raise NotImplementedError

class TableEncoder(Encoder):
    """
    Encoder to render app types into table format.
    """

    def encode(self, obj: object) -> str:
        if isinstance(obj, DatasetEntry):
            return self._as_row_pretty(obj)
        raise TypeError(f"Unsupported object type: {type(object)}")

    def get_header_pretty(self) -> str:
        row = (
            "| "
            "UID | "
            "Pool | "
            "Prompt | "
            "Weight | "
            "Sensitivity | "
            "Enabled | "
            "Flags |\n"
        )
        return row

    def _as_row_pretty(self, obj: DatasetEntry) -> str:
        row = (
            "| "
            f"{obj.uid} | "
            f"{obj.pool} | "
            f"{obj.prompt} | "
            f"{obj.weight} | "
            f"{obj.sensitivity} | "
            f"{obj.enabled} | "
            f"{obj.flags} |\n"
        )
        return row


class JsonEncoder(Encoder):
    """
    Encoder to render app types into JSON.
    """

    def encode(self, obj: object) -> dict:
        if isinstance(obj, DatasetEntry):
            return self._to_json_entry(obj)
        # Let the base class handle other unsupported types
        raise TypeError(f"Unsupported object type: {type(object)}")

    def _to_json_entry(self, obj: DatasetEntry) -> dict:
        data = {
            "text": obj.prompt
        }
        if obj.weight != 1:
            data["weight"] = obj.weight
        if obj.sensitivity != 'S':
            data["sensitivity"] = obj.sensitivity
        if not obj.enabled:
            data["enabled"] = False
        if obj.flags != "":
            data["flags"] = [flag.strip() for flag in obj.flags.split(",")]
        return data
