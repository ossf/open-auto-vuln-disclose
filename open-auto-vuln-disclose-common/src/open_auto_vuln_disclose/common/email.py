from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class EmailProcessingStep:
    identifier: str
    """Unique identifier for the individual instance of the vulnerability being disclosed to a single repository"""


@dataclass(frozen=True)
class SendingEmails(EmailProcessingStep):
    emails: List[str]


@dataclass(frozen=True)
class AwaitingEmailResponses(EmailProcessingStep):
    emails_sent: List[str]
    emails_bounced: List[str]
