import datetime
from typing import Union

from open_auto_vuln_disclose.common.issue import AwaitingIssue, IssuePhaseFinished, IssueNeeded, IssueProcessingState, \
    Issue
from open_auto_vuln_disclose.host.client import IssueClient


class MockHappyPathIssueClient(IssueClient):
    async def create_issue(
            self,
            issue_processing_step: IssueNeeded
    ) -> IssueProcessingState:
        return AwaitingIssue(
            identifier=issue_processing_step.identifier,
            repository=issue_processing_step.repository,
            issue=Issue(
                creation_date=datetime.datetime.now(tz=datetime.timezone.utc),
                issue_identifier='42',
                issue_url=f'{issue_processing_step.repository.as_url()}/issues/42',
            )
        )

    async def check_for_update(
            self,
            awaiting_issue_step: AwaitingIssue
    ) -> Union[AwaitingIssue, IssuePhaseFinished]:
        return awaiting_issue_step
