from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, auto
from typing import List, Optional


@dataclass(frozen=True)
class EmailProcessingState:
    identifier: str
    """Unique identifier for the individual instance of the vulnerability being disclosed to a single repository"""


@dataclass(frozen=True)
class EmailProcessingEndState(EmailProcessingState):
    """Marker class for the end states of the email processing state machine"""
    pass


@dataclass(frozen=True)
class EmailSendQueued(EmailProcessingState):
    emails: List[str]


@dataclass(frozen=True)
class SentEmails:
    send_date: datetime
    emails_sent: List[str]

    def __post_init__(self):
        if self.send_date.tzinfo is None:
            raise ValueError("send_date must have a timezone")


@dataclass(frozen=True)
class AwaitingEmailResponses(EmailProcessingState):
    emails_bounced: List[str]
    sent_emails: SentEmails


@dataclass(frozen=True)
class EmailResponseFixInvalid(EmailProcessingEndState):
    reason: str
    sent_emails: SentEmails


@dataclass(frozen=True)
class EmailResponseNotAVulnerability(EmailProcessingEndState):
    reason: str
    sent_emails: SentEmails


class EmailPhaseFinishedReason(StrEnum):
    NINETY_DAYS_PASSED = auto()
    ALL_EMAILS_BOUNCED = auto()
    AUTOMATED_PLEASE_FILL_FORM_RESPONSE = auto()
    NO_DISCLOSURE_EMAIL_FOUND = auto()


@dataclass(frozen=True)
class EmailPhaseFinished(EmailProcessingEndState):
    completed_reason: EmailPhaseFinishedReason
    sent_emails: Optional[SentEmails]
