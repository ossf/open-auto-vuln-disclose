import asyncio

from open_auto_vuln_disclose.common import Repository
from open_auto_vuln_disclose.host.host import RepositoryHost, PMPVR


class DisclosureOrchestrator:
    repository_host: RepositoryHost

    def __init__(self, repository_host: RepositoryHost):
        self.repository_host = repository_host

    async def do_disclosure(self, repository: Repository):
        pmpvr_disclosure_status = await self.do_pmpvr_disclosure(repository)
        if pmpvr_disclosure_status:
            # Disclosure was successful, no need to do anything else
            return None
        email_async = self.do_email_disclosure(repository)
        return await asyncio.gather(pmpvr_async, email_async)

    async def do_pmpvr_disclosure(self, repository: Repository):
        pmpvr = await self.repository_host.get_pmpvr()
        if pmpvr is None:
            return None
        if await pmpvr.repository_supports_pmpvr(repository):
            ...

    async def do_email_disclosure(self, repository: Repository):
        ...
