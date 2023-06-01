import abc
from typing import Type, Optional

from open_auto_vuln_disclose.common import Repository


class RepositoryHost(abc.ABC):

    @abc.abstractmethod
    async def get_pmpvr(self) -> Optional['PMPVR']:
        ...


class ProgrammaticMeansOfPrivateVulnerabilityDisclosure(abc.ABC):

    async def repository_supports_pmpvr(self, repository: Repository) -> bool:
        ...


PMPVR: Type[ProgrammaticMeansOfPrivateVulnerabilityDisclosure] = ProgrammaticMeansOfPrivateVulnerabilityDisclosure
