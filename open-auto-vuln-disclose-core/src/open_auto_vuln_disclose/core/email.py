import abc
from typing import List, Callable, Optional

from open_auto_vuln_disclose.common import Repository
from open_auto_vuln_disclose.common.util import callable_not_implemented_exception


class DisclosureEmailOracle(abc.ABC):

    @abc.abstractmethod
    async def find_disclosure_emails_for_repository(self, repository: Repository) -> List[str]:
        ...

    @staticmethod
    def from_callable(
            find_disclosure_emails_for_repository: Callable[[Repository], List[str]]
    ) -> 'DisclosureEmailOracle':
        assert isinstance(find_disclosure_emails_for_repository, Callable)

        class CallableDisclosureEmailOracle(DisclosureEmailOracle):

            async def find_disclosure_emails_for_repository(self, repository: Repository) -> List[str]:
                return find_disclosure_emails_for_repository(repository)

        return CallableDisclosureEmailOracle()

    @staticmethod
    def from_callable_for_test(
            find_disclosure_emails_for_repository: Callable[[Repository], List[str]] =
            callable_not_implemented_exception(
                "find_disclosure_emails_for_repository was called unexpectedly"
            )
    ):
        return DisclosureEmailOracle.from_callable(find_disclosure_emails_for_repository)
