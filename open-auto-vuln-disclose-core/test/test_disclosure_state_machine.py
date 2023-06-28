import datetime
import unittest
from typing import List, Optional

from mock_email_client import MockHappyPathEmailClient
from mock_issue_client import MockHappyPathIssueClient
from open_auto_vuln_disclose.common import Repository
from open_auto_vuln_disclose.common.disclosure import DisclosureProcessingStep, DisclosureState
from open_auto_vuln_disclose.common.email import EmailSendQueued, AwaitingEmailResponses, SentEmails, \
    EmailPhaseFinished, EmailPhaseFinishedReason
from open_auto_vuln_disclose.common.issue import AwaitingIssue, IssueNeeded, Issue, IssuePhaseFinished, \
    IssuePhaseFinishedReason
from open_auto_vuln_disclose.common.timeline import LiveDisclosureSpecification, DisclosureSpecification
from open_auto_vuln_disclose.core.email import DisclosureEmailOracle
from open_auto_vuln_disclose.core.state_machine import DisclosureStateMachine
from open_auto_vuln_disclose.email.client import EmailClient
from open_auto_vuln_disclose.email.state_machine import EmailStateMachine
from open_auto_vuln_disclose.host.client import IssueClient
from open_auto_vuln_disclose.host.state_machine import IssueStateMachine

REPOSITORY = Repository(
    host='github.com',
    owner='test-owner',
    name='test-name',
)


class DisclosureStateMachineTestCase(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def create_disclosure_state_machine(
            disclosure_email_oracle: DisclosureEmailOracle = DisclosureEmailOracle.from_callable_for_test(),
            email_client: EmailClient = EmailClient.from_callable_for_test(),
            issue_client: IssueClient = EmailClient.from_callable_for_test(),
            disclosure_specification: DisclosureSpecification = LiveDisclosureSpecification(),
    ) -> DisclosureStateMachine:
        return DisclosureStateMachine(
            disclosure_email_oracle=disclosure_email_oracle,
            email_state_machine=EmailStateMachine(
                email_client=email_client,
                disclosure_specification=disclosure_specification,
            ),
            issue_state_machine=IssueStateMachine(
                issue_client=issue_client,
                disclosure_specification=disclosure_specification,
            ),
        )

    @staticmethod
    def create_initial_disclosure_processing_step() -> DisclosureProcessingStep:
        return DisclosureProcessingStep.create_minimal_initial(
            identifier='test-identifier',
            campaign_identifier='test-campaign-identifier',
            repository=REPOSITORY,
        )

    def assert_well_formed_disclosure_state(
            self,
            initial: DisclosureProcessingStep,
            processed: DisclosureProcessingStep,
    ):
        self.assertEqual(
            processed.identifier,
            initial.identifier,
        )
        self.assertEqual(
            processed.campaign_identifier,
            initial.campaign_identifier,
        )
        self.assertEqual(
            processed.repository,
            initial.repository,
        )
        if processed.issue_processing_state is not None:
            self.assertEqual(
                processed.issue_processing_state.identifier,
                initial.identifier,
            )
            self.assertEqual(
                processed.issue_processing_state.repository,
                initial.repository,
            )
        if processed.email_processing_state is not None:
            self.assertEqual(
                processed.email_processing_state.identifier,
                initial.identifier,
            )

    async def test_minimal_disclosure_processing_step_gets_details_filled_in(self):
        initial = self.create_initial_disclosure_processing_step()
        disclosure_state_machine = self.create_disclosure_state_machine(
            disclosure_email_oracle=DisclosureEmailOracle.from_callable_for_test(lambda _: ["example@example.com"]),
        )
        processed = await disclosure_state_machine.process_state_transition(initial)
        self.assert_well_formed_disclosure_state(initial, processed)
        self.assertIsInstance(processed.email_processing_state, EmailSendQueued)
        self.assertEqual(
            processed.email_processing_state.identifier,
            initial.identifier,
        )
        self.assertEqual(
            processed.email_processing_state.emails,
            ["example@example.com"],
        )
        self.assertIsInstance(processed.issue_processing_state, IssueNeeded)
        self.assertEqual(
            processed.issue_processing_state.identifier,
            initial.identifier,
        )

    async def create_initialized_disclosure_processing_step(
            self,
            disclosure_emails: Optional[List[str]] = None,
    ) -> DisclosureProcessingStep:
        if disclosure_emails is None:
            disclosure_emails = ["example@example.com"]
        initial = self.create_initial_disclosure_processing_step()
        disclosure_state_machine = self.create_disclosure_state_machine(
            disclosure_email_oracle=DisclosureEmailOracle.from_callable_for_test(lambda _: disclosure_emails),
        )
        return await disclosure_state_machine.process_state_transition(initial)

    async def test_initialized_disclosure_processing_step_gets_processed_happy_path(self):
        # Given: an initialized disclosure processing step
        initialized = await self.create_initialized_disclosure_processing_step()
        # And: The disclosure state machine sees that email sending and issue creation succeeded
        disclosure_state_machine = self.create_disclosure_state_machine(
            email_client=MockHappyPathEmailClient(),
            issue_client=MockHappyPathIssueClient(),
        )
        # When: The disclosure state machine processes the step
        processed = await disclosure_state_machine.process_state_transition(initialized)

        # Then: The disclosure state machine has updated the state
        self.assert_well_formed_disclosure_state(initialized, processed)
        self.assertIsInstance(processed.issue_processing_state, AwaitingIssue)
        self.assertIsInstance(processed.email_processing_state, AwaitingEmailResponses)
        self.assertEqual(processed.disclosure_state, DisclosureState.AWAITING_PMPVR_ENABLE)

        # When: The disclosure state machine processes the step again
        processed = await disclosure_state_machine.process_state_transition(processed)

        # Then: The disclosure state machine has updated not updated the state
        self.assert_well_formed_disclosure_state(initialized, processed)
        self.assertIsInstance(processed.issue_processing_state, AwaitingIssue)
        self.assertIsInstance(processed.email_processing_state, AwaitingEmailResponses)
        self.assertEqual(processed.disclosure_state, DisclosureState.AWAITING_PMPVR_ENABLE)

        # When: A disclosure state machine processes the step again 95 days in the future
        future_disclosure_state_machine = self.create_disclosure_state_machine(
            disclosure_specification=DisclosureSpecification.fixed_time_for_testing(
                processed.email_processing_state.sent_emails.send_date + datetime.timedelta(days=95),
            )
        )
        processed = await future_disclosure_state_machine.process_state_transition(processed)

        # Then: The disclosure state machine has updated the state
        self.assert_well_formed_disclosure_state(initialized, processed)
        self.assertIsInstance(processed.issue_processing_state, IssuePhaseFinished)
        self.assertEqual(
            processed.issue_processing_state.completed_reason,
            IssuePhaseFinishedReason.THIRTY_FIVE_DAYS_PASSED
        )
        self.assertIsInstance(processed.email_processing_state, EmailPhaseFinished)
        self.assertEqual(
            processed.email_processing_state.completed_reason,
            EmailPhaseFinishedReason.NINETY_DAYS_PASSED
        )
        self.assertEqual(processed.disclosure_state, DisclosureState.DISCLOSE_VIA_PUBLIC_PULL_REQUEST)

        # When: A disclosure state machine processes the step again
        future_disclosure_state_machine = self.create_disclosure_state_machine()
        previous_processed = processed
        processed = await future_disclosure_state_machine.process_state_transition(previous_processed)
        # Then: The disclosure state machine has not modified the state
        self.assertEqual(processed, previous_processed)

    async def test_initialized_disclosure_processing_step_gets_processed_when_no_emails_are_found(self):
        # Given: an initialized disclosure processing step
        initialized = await self.create_initialized_disclosure_processing_step(disclosure_emails=[])
        # And: The disclosure state machine sees that email sending and issue creation succeeded
        disclosure_state_machine = self.create_disclosure_state_machine(
            issue_client=MockHappyPathIssueClient(),
        )
        # When: The disclosure state machine processes the step
        processed = await disclosure_state_machine.process_state_transition(initialized)
        self.assert_well_formed_disclosure_state(initialized, processed)
        self.assertIsInstance(processed.issue_processing_state, AwaitingIssue)
        self.assertIsInstance(processed.email_processing_state, EmailPhaseFinished)
        self.assertEqual(
            processed.email_processing_state.completed_reason,
            EmailPhaseFinishedReason.NO_DISCLOSURE_EMAIL_FOUND
        )
        self.assertIsNone(processed.email_processing_state.sent_emails)


if __name__ == '__main__':
    unittest.main()
