from typing import Optional

from open_auto_vuln_disclose.host.host import RepositoryHost, PMPVR


class GitHubRepositoryHost(RepositoryHost):
    async def get_pmpvr(self) -> Optional['PMPVR']:
        pass
