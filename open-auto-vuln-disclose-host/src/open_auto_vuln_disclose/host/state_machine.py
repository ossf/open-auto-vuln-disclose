from open_auto_vuln_disclose.common.timeline import DisclosureSpecification
from open_auto_vuln_disclose.common.issue import IssueProcessingState, IssuePhaseFinished, IssueNeeded, AwaitingIssue, \
    IssuePhaseFinishedReason
from open_auto_vuln_disclose.host.client import IssueClient


class IssueStateMachine:
    _issue_client: IssueClient
    _disclosure_specification: DisclosureSpecification

    def __init__(self, issue_client: IssueClient, disclosure_specification: DisclosureSpecification):
        self._issue_client = issue_client
        self._disclosure_specification = disclosure_specification

    async def process_state_transition(self, issue_processing_step: IssueProcessingState) -> IssueProcessingState:
        if isinstance(issue_processing_step, IssuePhaseFinished):
            # Issue processing is in the 'end' state, no state transition to process
            return issue_processing_step
        if isinstance(issue_processing_step, IssueNeeded):
            # Issue is needed, try to create it
            return await self._issue_client.create_issue(issue_processing_step)
        if isinstance(issue_processing_step, AwaitingIssue):
            if self._disclosure_specification.is_issue_pmpvr_request_deadline_met(
                    issue_processing_step.issue.creation_date):
                # Issue is awaiting response, check for updates
                return IssuePhaseFinished(
                    identifier=issue_processing_step.identifier,
                    repository=issue_processing_step.repository,
                    completed_reason=IssuePhaseFinishedReason.THIRTY_FIVE_DAYS_PASSED,
                    issue=issue_processing_step.issue,
                )
            return await self._issue_client.check_for_update(issue_processing_step)

        raise NotImplementedError("Unknown issue processing step type: {}".format(type(issue_processing_step).__name__))
