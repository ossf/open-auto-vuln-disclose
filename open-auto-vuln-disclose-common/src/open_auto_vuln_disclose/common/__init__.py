import dataclasses
from enum import StrEnum, auto


@dataclasses.dataclass(frozen=True)
class Repository:
    host: str
    owner: str
    name: str

    def as_url(self):
        return f"https://{self.host}/{self.owner}/{self.name}"


class DisclosureState(StrEnum):
    DISCLOSURE_QUEUED = auto()
    AWAITING_PMPVR_ENABLE = auto()
    DISCLOSE_VIA_PMPVR = auto()
    DISCLOSE_VIA_PUBLIC_PULL_REQUEST = auto()
    COMPLETE_REPOSITORY_ARCHIVED = auto()
    COMPLETE_DISCLOSED_VIA_PMPVR = auto()
    COMPLETE_DISCLOSED_VIA_PUBLIC_PULL_REQUEST = auto()
    COMPLETE_INVALID_FIX = auto()
