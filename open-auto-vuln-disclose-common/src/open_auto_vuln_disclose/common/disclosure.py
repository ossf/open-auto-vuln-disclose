from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Optional, List

from open_auto_vuln_disclose.common import Repository
from open_auto_vuln_disclose.common.email import EmailProcessingState
from open_auto_vuln_disclose.common.issue import IssueProcessingState


class DisclosureState(StrEnum):
    DISCLOSURE_QUEUED = auto()
    AWAITING_PMPVR_ENABLE = auto()
    DISCLOSE_VIA_PMPVR = auto()
    DISCLOSE_VIA_PUBLIC_FORK = auto()
    DISCLOSE_VIA_PUBLIC_PULL_REQUEST = auto()
    COMPLETE_REPOSITORY_ARCHIVED = auto()
    COMPLETE_DISCLOSED_VIA_PMPVR = auto()
    COMPLETE_DISCLOSED_VIA_PUBLIC_FORK = auto()
    COMPLETE_DISCLOSED_VIA_PUBLIC_PULL_REQUEST = auto()
    COMPLETE_INVALID_FIX = auto()

    @classmethod
    def completed_states(cls) -> List['DisclosureState']:
        return [
            cls.COMPLETE_REPOSITORY_ARCHIVED,
            cls.COMPLETE_DISCLOSED_VIA_PMPVR,
            cls.COMPLETE_DISCLOSED_VIA_PUBLIC_PULL_REQUEST,
            cls.COMPLETE_INVALID_FIX
        ]


@dataclass(frozen=True)
class DisclosureProcessingStep:
    """
    Represents the current state of a disclosure for a single repository, for a single instance of a vulnerability.

    Best practices to create instances of this class is to use the `create_minimal_initial()` method.
    """
    identifier: str
    campaign_identifier: str
    """
    Opaque identifier for the campaign that this disclosure is part of.
    This is used to group together disclosures that are part of the same campaign.
    """
    repository: Repository
    disclosure_state: DisclosureState
    issue_processing_state: Optional[IssueProcessingState]
    email_processing_state: Optional[EmailProcessingState]

    def is_complete(self) -> bool:
        return self.disclosure_state in DisclosureState.completed_states()

    @staticmethod
    def create_minimal_initial(
            identifier: str,
            campaign_identifier: str,
            repository: Repository,
    ) -> 'DisclosureProcessingStep':
        return DisclosureProcessingStep(
            identifier=identifier,
            campaign_identifier=campaign_identifier,
            repository=repository,
            disclosure_state=DisclosureState.DISCLOSURE_QUEUED,
            issue_processing_state=None,
            email_processing_state=None,
        )
