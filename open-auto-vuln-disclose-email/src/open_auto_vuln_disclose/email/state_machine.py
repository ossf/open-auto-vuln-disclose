from open_auto_vuln_disclose.common.timeline import DisclosureSpecification
from open_auto_vuln_disclose.common.email import EmailProcessingState, EmailPhaseFinished, EmailSendQueued, \
    AwaitingEmailResponses, EmailPhaseFinishedReason, EmailProcessingEndState

from open_auto_vuln_disclose.email.client import EmailClient


class EmailStateMachine:
    _email_client: EmailClient
    _disclosure_specification: DisclosureSpecification

    def __init__(self, email_client: EmailClient, disclosure_specification: DisclosureSpecification):
        self._email_client = email_client
        self._disclosure_specification = disclosure_specification

    async def process_state_transition(self, email_processing_step: EmailProcessingState) -> EmailProcessingState:
        assert isinstance(email_processing_step, EmailProcessingState)
        if isinstance(email_processing_step, EmailProcessingEndState):
            # Email processing is in the 'end' state, no state transition to process
            return email_processing_step
        if isinstance(email_processing_step, EmailSendQueued):
            # Email is queued to be sent, try to send it
            return await self._email_client.send_email(email_processing_step)
        if isinstance(email_processing_step, AwaitingEmailResponses):
            # Email has been sent, first check if 90 days have elapsed since the email was sent
            if self._disclosure_specification.is_email_disclosure_deadline_met(
                    email_processing_step.sent_emails.send_date
            ):
                # 90 days have elapsed, disclose
                return EmailPhaseFinished(
                    identifier=email_processing_step.identifier,
                    completed_reason=EmailPhaseFinishedReason.NINETY_DAYS_PASSED,
                    sent_emails=email_processing_step.sent_emails
                )
            # 90 days have not elapsed, check for responses
            return await self._email_client.check_for_email_responses(email_processing_step)
        raise NotImplementedError("Unknown issue processing step type: {}".format(type(email_processing_step).__name__))
