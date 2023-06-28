import abc
from typing import Type, Optional, Union, Callable

from open_auto_vuln_disclose.common import Repository
from open_auto_vuln_disclose.common.issue import IssueNeeded, IssueProcessingState, AwaitingIssue, IssuePhaseFinished
from open_auto_vuln_disclose.common.util import callable_not_implemented_exception


class RepositoryHostClient(abc.ABC):

    @abc.abstractmethod
    async def get_pmpvr_client(self) -> Optional['PMPVRClient']:
        ...

    @abc.abstractmethod
    async def get_issue_client(self) -> 'IssueClient':
        ...


class ProgrammaticMeansOfPrivateVulnerabilityDisclosureClient(abc.ABC):

    async def repository_supports_pmpvr(self, repository: Repository) -> bool:
        ...


PMPVRClient: Type[ProgrammaticMeansOfPrivateVulnerabilityDisclosureClient] = \
    ProgrammaticMeansOfPrivateVulnerabilityDisclosureClient


class IssueClient(abc.ABC):
    @abc.abstractmethod
    async def create_issue(self, issue_processing_step: IssueNeeded) -> IssueProcessingState:
        ...

    @abc.abstractmethod
    async def check_for_update(self, awaiting_issue_step: AwaitingIssue) -> Union[
        AwaitingIssue, IssuePhaseFinished
    ]:
        ...

    @staticmethod
    def from_callable(
            create_issue_response: Callable[[IssueNeeded], IssueProcessingState],
            check_for_update_response: Callable[[AwaitingIssue], Union[AwaitingIssue, IssuePhaseFinished]]
    ):
        assert isinstance(create_issue_response, Callable)
        assert isinstance(check_for_update_response, Callable)

        class CallableIssueClient(IssueClient):

            async def create_issue(self, issue_processing_step: IssueNeeded) -> IssueProcessingState:
                return create_issue_response(issue_processing_step)

            async def check_for_update(self, awaiting_issue_step: AwaitingIssue) -> Union[
                AwaitingIssue, IssuePhaseFinished
            ]:
                return check_for_update_response(awaiting_issue_step)

        return CallableIssueClient()

    @staticmethod
    def from_callable_for_test(
            create_issue_response: Optional[Callable[[IssueNeeded], IssueProcessingState]] =
            callable_not_implemented_exception(
                "create_issue_response was called unexpectedly"
            ),
            check_for_update_response: Optional[Callable[[AwaitingIssue], Union[AwaitingIssue, IssuePhaseFinished]]] =
            callable_not_implemented_exception(
                "check_for_update_response was called unexpectedly"
            )
    ):
        return IssueClient.from_callable(
            create_issue_response=create_issue_response,
            check_for_update_response=check_for_update_response
        )
