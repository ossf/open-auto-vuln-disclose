from typing import Optional

from open_auto_vuln_disclose.host.client import RepositoryHostClient, PMPVRClient


class GitHubRepositoryHost(RepositoryHostClient):
    async def get_pmpvr_client(self) -> Optional['PMPVRClient']:
        pass
