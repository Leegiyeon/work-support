from typing import BinaryIO, Protocol


class ObjectStorage(Protocol):
    """Future storage boundary for uploaded originals.

    Implementations must preserve owner-scoped paths and never expose public
    object URLs by default. Upload endpoints are intentionally not implemented
    in this scaffold; this protocol only fixes the future contract boundary.
    """

    root: str

    def build_owner_path(self, owner_id: str, filename: str) -> str:
        """Return a non-public storage path scoped to one owner."""

    def save_original(self, owner_id: str, filename: str, content: BinaryIO) -> str:
        """Persist an uploaded original and return its owner-scoped path."""

    def open_original(self, owner_id: str, storage_path: str) -> BinaryIO:
        """Open an owner-scoped original without exposing a public URL."""
