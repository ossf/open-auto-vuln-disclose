import dataclasses


@dataclasses.dataclass(frozen=True)
class Repository:
    host: str
    owner: str
    name: str

    def as_url(self):
        return f"https://{self.host}/{self.owner}/{self.name}"

