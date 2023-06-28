import datetime
from typing import Union

from open_auto_vuln_disclose.common.email import AwaitingEmailResponses, EmailProcessingEndState, EmailSendQueued, \
    SentEmails
from open_auto_vuln_disclose.email.client import EmailClient


class MockHappyPathEmailClient(EmailClient):
    async def send_email(
            self,
            email_processing_step: EmailSendQueued
    ) -> Union[EmailSendQueued, AwaitingEmailResponses]:
        return AwaitingEmailResponses(
            identifier=email_processing_step.identifier,
            emails_bounced=[],
            sent_emails=SentEmails(
                send_date=datetime.datetime.now(tz=datetime.timezone.utc),
                emails_sent=email_processing_step.emails,
            )
        )

    async def check_for_email_responses(
            self,
            email_processing_step: AwaitingEmailResponses
    ) -> Union[AwaitingEmailResponses, EmailProcessingEndState]:
        return email_processing_step
