from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, auto
from typing import Optional

from open_auto_vuln_disclose.common import Repository


@dataclass(frozen=True)
class IssueProcessingState:
    identifier: str
    """
    Unique identifier for the repository being disclosed to.
    This is used instead of the URL to handle cases where the issue is deleted, moved, or turned into a discussion.
    """
    repository: Repository


@dataclass(frozen=True)
class IssueNeeded(IssueProcessingState):
    """
    Pending the creation of an issue.
    """
    pass


@dataclass(frozen=True)
class Issue:
    """
    Represents an issue that has actually been created on a repository.
    Not a state, but a dataclass that is used in multiple states.
    """
    creation_date: datetime
    issue_identifier: str
    issue_url: str

    def __post_init__(self):
        if self.creation_date.tzinfo is None:
            raise ValueError("creation_date must have a timezone")


@dataclass(frozen=True)
class AwaitingIssue(IssueProcessingState):
    issue: Issue


class IssuePhaseFinishedReason(StrEnum):
    THIRTY_FIVE_DAYS_PASSED = auto()
    ISSUE_CLOSED_NO_RESPONSE = auto()
    ISSUE_CLOSED_BY_STALE_AUTOMATION = auto()
    ISSUES_UNSUPPORTED = auto()


@dataclass(frozen=True)
class IssuePhaseFinished(IssueProcessingState):
    completed_reason: IssuePhaseFinishedReason
    issue: Optional[Issue]
