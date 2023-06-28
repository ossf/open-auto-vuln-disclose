import dataclasses

from open_auto_vuln_disclose.common.disclosure import DisclosureProcessingStep, DisclosureState
from open_auto_vuln_disclose.common.email import EmailSendQueued, EmailProcessingState, EmailPhaseFinished, \
    EmailPhaseFinishedReason
from open_auto_vuln_disclose.common.issue import IssueProcessingState, IssueNeeded, IssuePhaseFinished
from open_auto_vuln_disclose.core.email import DisclosureEmailOracle
from open_auto_vuln_disclose.email.state_machine import EmailStateMachine
from open_auto_vuln_disclose.host.state_machine import IssueStateMachine


class DisclosureStateMachine:
    disclosure_email_oracle: DisclosureEmailOracle
    email_state_machine: EmailStateMachine
    issue_state_machine: IssueStateMachine

    def __init__(
            self,
            disclosure_email_oracle: DisclosureEmailOracle,
            email_state_machine: EmailStateMachine,
            issue_state_machine: IssueStateMachine,
    ):
        self.disclosure_email_oracle = disclosure_email_oracle
        self.email_state_machine = email_state_machine
        self.issue_state_machine = issue_state_machine

    async def process_state_transition(
            self,
            disclosure_processing_step: DisclosureProcessingStep
    ) -> DisclosureProcessingStep:
        if disclosure_processing_step.is_complete():
            return disclosure_processing_step

        email_processing_state: EmailProcessingState
        if disclosure_processing_step.email_processing_state is None:
            # No email processing state, need to create one
            disclosure_emails = await self.disclosure_email_oracle.find_disclosure_emails_for_repository(
                disclosure_processing_step.repository
            )
            if len(disclosure_emails) == 0:
                # No emails found, need to create a state for that
                email_processing_state = EmailPhaseFinished(
                    identifier=disclosure_processing_step.identifier,
                    completed_reason=EmailPhaseFinishedReason.NO_DISCLOSURE_EMAIL_FOUND,
                    sent_emails=None,
                )
            else:
                email_processing_state = EmailSendQueued(
                    identifier=disclosure_processing_step.identifier,
                    emails=disclosure_emails
                )
        else:
            email_processing_state = disclosure_processing_step.email_processing_state
        issue_processing_state: IssueProcessingState
        if disclosure_processing_step.issue_processing_state is None:
            issue_processing_state = IssueNeeded(
                identifier=disclosure_processing_step.identifier,
                repository=disclosure_processing_step.repository
            )
        else:
            issue_processing_state = disclosure_processing_step.issue_processing_state

        next_disclosure_processing_step = dataclasses.replace(
            disclosure_processing_step,
            email_processing_state=email_processing_state,
            issue_processing_state=issue_processing_state,
        )
        if next_disclosure_processing_step != disclosure_processing_step:
            # Something changed, need to save the new state
            return next_disclosure_processing_step

        # Nothing has changed, need to process the next state transition
        next_email_processing_state_async = self.email_state_machine.process_state_transition(
            email_processing_state
        )
        next_issue_processing_state_async = self.issue_state_machine.process_state_transition(
            issue_processing_state
        )
        next_email_processing_state = await next_email_processing_state_async
        next_issue_processing_state = await next_issue_processing_state_async
        next_disclosure_processing_step = dataclasses.replace(
            disclosure_processing_step,
            email_processing_state=next_email_processing_state,
            issue_processing_state=next_issue_processing_state,
        )
        # If emails have been sent, and an issue has been created, we are now awaiting PMPVR enablement
        if not (
                isinstance(next_email_processing_state, EmailSendQueued) and
                isinstance(next_issue_processing_state, IssueNeeded)
        ) and next_disclosure_processing_step.disclosure_state is DisclosureState.DISCLOSURE_QUEUED:
            # Email and issue processing have both started, we are now awaiting PMPVR enablement
            return dataclasses.replace(
                next_disclosure_processing_step,
                disclosure_state=DisclosureState.AWAITING_PMPVR_ENABLE
            )
        # If email and issues are both in a public disclosure state, then publicly disclose via public pull request
        if (isinstance(next_email_processing_state, EmailPhaseFinished) and
                isinstance(next_issue_processing_state, IssuePhaseFinished) and
                next_disclosure_processing_step.disclosure_state is DisclosureState.AWAITING_PMPVR_ENABLE):
            return dataclasses.replace(
                next_disclosure_processing_step,
                disclosure_state=DisclosureState.DISCLOSE_VIA_PUBLIC_PULL_REQUEST
            )
        return next_disclosure_processing_step
