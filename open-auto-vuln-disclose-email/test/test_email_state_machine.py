import unittest
from datetime import datetime, timezone, timedelta

from parameterized import parameterized

from open_auto_vuln_disclose.common.timeline import DisclosureSpecification
from open_auto_vuln_disclose.common.email import AwaitingEmailResponses, EmailProcessingEndState, EmailSendQueued, \
    SentEmails, EmailResponseFixInvalid, EmailResponseNotAVulnerability, EmailPhaseFinishedReason, EmailPhaseFinished
from open_auto_vuln_disclose.email.state_machine import EmailStateMachine
from open_auto_vuln_disclose.email.client import EmailClient

EXAMPLE_EMAIL_ADDRESS = "example@example.com"
SENT_EMAILS = SentEmails(
    send_date=datetime(2021, 1, 1, tzinfo=timezone.utc),
    emails_sent=[EXAMPLE_EMAIL_ADDRESS]
)


class EmailTestCase(unittest.IsolatedAsyncioTestCase):

    @staticmethod
    def create_email_state_machine(
            email_client: EmailClient,
            deadline_manager: DisclosureSpecification = DisclosureSpecification.live(),
    ) -> EmailStateMachine:
        return EmailStateMachine(
            email_client=email_client,
            disclosure_specification=deadline_manager
        )

    @parameterized.expand([
        (EmailResponseFixInvalid("1", "The Reason", SENT_EMAILS),),
        (EmailResponseNotAVulnerability("2", "The Reason", SENT_EMAILS),),
        (EmailPhaseFinished("3", EmailPhaseFinishedReason.NINETY_DAYS_PASSED, SENT_EMAILS),),
    ])
    async def test_finished_state_always_returns_self(self, email_processing_step: EmailProcessingEndState):
        # Given: A no-op email client
        manager = self.create_email_state_machine(EmailClient.from_callable_for_test())
        # When: We process a finished state
        new_state = await manager.process_state_transition(email_processing_step)
        # Then: The state is unchanged
        self.assertEqual(new_state, email_processing_step)

    async def test_send_email_fails(self):
        # An email client that always fails to send an email
        manager = self.create_email_state_machine(EmailClient.from_callable_for_test(
            send_email_response=lambda state: state
        ))
        # When: We process a queued email
        queued = EmailSendQueued("1", [EXAMPLE_EMAIL_ADDRESS])
        new_state = await manager.process_state_transition(queued)
        # Then: The state is unchanged
        self.assertEqual(new_state, queued)

    async def test_send_email_succeeds(self):
        # An email client that always succeeds to send an email
        manager = self.create_email_state_machine(EmailClient.from_callable_for_test(
            send_email_response=lambda state: AwaitingEmailResponses(
                identifier=state.identifier,
                emails_bounced=[],
                sent_emails=SENT_EMAILS,
            )
        ))
        # When: We process a queued email
        queued = EmailSendQueued("1", [EXAMPLE_EMAIL_ADDRESS])
        new_state = await manager.process_state_transition(queued)
        # Then: The state is changed to AwaitingEmailResponses
        self.assertEqual(new_state, AwaitingEmailResponses(
            identifier=queued.identifier,
            emails_bounced=[],
            sent_emails=SENT_EMAILS,
        ))

    async def test_check_for_email_responses_has_no_new_responses(self):
        # An email client that always has no new responses
        manager = self.create_email_state_machine(
            email_client=EmailClient.from_callable_for_test(
                check_for_email_responses_response=lambda state: state,
            ),
            deadline_manager=DisclosureSpecification.fixed_time_for_testing(SENT_EMAILS.send_date),
        )
        # When: We process an awaiting email responses
        awaiting = AwaitingEmailResponses(
            identifier="1",
            emails_bounced=[],
            sent_emails=SENT_EMAILS,
        )
        new_state = await manager.process_state_transition(awaiting)
        # Then: The state is unchanged
        self.assertEqual(new_state, awaiting)

    async def test_disclosure_deadline_passed(self):
        # A manager being called when the disclosure deadline has passed
        manager = self.create_email_state_machine(
            email_client=EmailClient.from_callable_for_test(),
            deadline_manager=DisclosureSpecification.fixed_time_for_testing(SENT_EMAILS.send_date + timedelta(days=91)),
        )
        # When: We process an awaiting email responses
        awaiting = AwaitingEmailResponses(
            identifier="1",
            emails_bounced=[],
            sent_emails=SENT_EMAILS,
        )
        new_state = await manager.process_state_transition(awaiting)
        # Then: The state is changed to EmailPhaseFinished
        self.assertEqual(
            new_state,
            EmailPhaseFinished(
                identifier=awaiting.identifier,
                completed_reason=EmailPhaseFinishedReason.NINETY_DAYS_PASSED,
                sent_emails=SENT_EMAILS,
            )
        )


if __name__ == '__main__':
    unittest.main()
