import unittest
from datetime import timezone, datetime, timedelta

from open_auto_vuln_disclose.common import Repository
from open_auto_vuln_disclose.common.timeline import DisclosureSpecification
from open_auto_vuln_disclose.common.issue import IssueNeeded, IssuePhaseFinished, \
    IssuePhaseFinishedReason, Issue, AwaitingIssue
from open_auto_vuln_disclose.host.client import IssueClient
from open_auto_vuln_disclose.host.state_machine import IssueStateMachine

REPOSITORY = Repository(
    host="github.com",
    owner="ossf",
    name="open-auto-vuln-disclose",
)


class HostTestCase(unittest.IsolatedAsyncioTestCase):

    @staticmethod
    def create_issue_state_machine(
            issue_client: IssueClient,
            deadline_manager: DisclosureSpecification = DisclosureSpecification.live(),
    ):
        return IssueStateMachine(
            issue_client,
            deadline_manager,
        )

    async def test_finished_state_always_returns_self(self):
        # Given: A no-op issue client
        manager = self.create_issue_state_machine(IssueClient.from_callable_for_test())
        issue_needed = IssuePhaseFinished(
            identifier="1",
            repository=REPOSITORY,
            completed_reason=IssuePhaseFinishedReason.ISSUES_UNSUPPORTED,
            issue=None,
        )
        response = await manager.process_state_transition(issue_needed)
        self.assertEqual(response, issue_needed)

    async def test_issue_needed_creates_issue(self):
        the_issue = Issue(
            creation_date=datetime.now(timezone.utc),
            issue_identifier="1",
            issue_url="https://github.com/example/example/issues/1",
        )
        manager = self.create_issue_state_machine(IssueClient.from_callable_for_test(
            create_issue_response=lambda issue_processing_step: AwaitingIssue(
                identifier=issue_processing_step.identifier,
                repository=issue_processing_step.repository,
                issue=the_issue,
            )
        ))
        issue_needed = IssueNeeded(
            identifier="1",
            repository=REPOSITORY,
        )
        response = await manager.process_state_transition(issue_needed)
        self.assertEqual(response, AwaitingIssue(
            identifier=issue_needed.identifier,
            repository=issue_needed.repository,
            issue=the_issue,
        ))

    async def test_issue_creation_fails(self):
        manager = self.create_issue_state_machine(IssueClient.from_callable_for_test(
            create_issue_response=lambda issue_processing_step: issue_processing_step
        ))
        issue_needed = IssueNeeded(
            identifier="1",
            repository=REPOSITORY,
        )
        new_state = await manager.process_state_transition(issue_needed)
        self.assertEqual(new_state, issue_needed)

    async def test_check_for_issue_responses_has_no_new_responses(self):
        manager = self.create_issue_state_machine(IssueClient.from_callable_for_test(
            check_for_update_response=lambda issue_processing_step: issue_processing_step
        ))
        awaiting_issue = AwaitingIssue(
            identifier="1",
            repository=REPOSITORY,
            issue=Issue(
                creation_date=datetime.now(timezone.utc),
                issue_identifier="1",
                issue_url="https://github.com/example/example/issues/1",
            )
        )
        new_state = await manager.process_state_transition(awaiting_issue)
        self.assertEqual(new_state, awaiting_issue)

    async def test_check_for_issue_responses_closed_without_response(self):
        manager = self.create_issue_state_machine(
            IssueClient.from_callable_for_test(
                check_for_update_response=lambda issue_processing_step: IssuePhaseFinished(
                    identifier=issue_processing_step.identifier,
                    repository=issue_processing_step.repository,
                    completed_reason=IssuePhaseFinishedReason.ISSUE_CLOSED_NO_RESPONSE,
                    issue=issue_processing_step.issue,
                )
            )
        )
        awaiting_issue = AwaitingIssue(
            identifier="1",
            repository=REPOSITORY,
            issue=Issue(
                creation_date=datetime.now(timezone.utc),
                issue_identifier="1",
                issue_url="https://github.com/example/example/issues/1",
            )
        )
        new_state = await manager.process_state_transition(awaiting_issue)
        self.assertEqual(new_state, IssuePhaseFinished(
            identifier=awaiting_issue.identifier,
            repository=awaiting_issue.repository,
            completed_reason=IssuePhaseFinishedReason.ISSUE_CLOSED_NO_RESPONSE,
            issue=awaiting_issue.issue,
        ))

    async def test_request_deadline_passed(self):
        the_issue = Issue(
            creation_date=datetime.now(timezone.utc),
            issue_identifier="1",
            issue_url="https://github.com/example/example/issues/1",
        )

        manager = self.create_issue_state_machine(
            IssueClient.from_callable_for_test(
                check_for_update_response=lambda issue_processing_step: issue_processing_step
            ),
            deadline_manager=DisclosureSpecification.fixed_time_for_testing(
                the_issue.creation_date + timedelta(days=36)
            )
        )
        awaiting_issue = AwaitingIssue(
            identifier="1",
            repository=REPOSITORY,
            issue=the_issue,
        )
        new_state = await manager.process_state_transition(awaiting_issue)
        self.assertEqual(new_state, IssuePhaseFinished(
            identifier=awaiting_issue.identifier,
            repository=awaiting_issue.repository,
            completed_reason=IssuePhaseFinishedReason.THIRTY_FIVE_DAYS_PASSED,
            issue=awaiting_issue.issue,
        ))


if __name__ == '__main__':
    unittest.main()
