from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable


class DisclosureSpecification(ABC):

    @abstractmethod
    def is_email_disclosure_deadline_met(self, contact_date: datetime) -> bool:
        """
        Check if disclosure should occur because of the number of days that have elapsed since the contact date.

        Disclose in the following cases:
          - It's a weekday
          - 90 days have elapsed since the contact date
        :param contact_date: The datetime that the emails were sent.
        :return: True if disclosure should occur, False otherwise.
        """
        ...

    @abstractmethod
    def is_issue_pmpvr_request_deadline_met(self, contact_date: datetime) -> bool:
        """
        Check if the PMPVR request deadline has passed.
        The deadline has passed if:
         - It's a weekday
         - 35 days have elapsed since the contact date
        :param contact_date:
        :return:
        """
        ...

    @staticmethod
    def live() -> "DisclosureSpecification":
        """
        Create a disclosure specification that uses the current time to determine if disclosure should occur.
        """
        return LiveDisclosureSpecification()

    @staticmethod
    def fixed_time_for_testing(now: datetime) -> "DisclosureSpecification":
        """
        Create a disclosure specification that uses the given datetime to determine if disclosure should occur.

        This should only be used for testing. In production, use the live() method to create a disclosure specification.
        :param now: The datetime to use to determine if disclosure should occur.
        """
        return _FixedTimeDisclosureSpecification(now)


@dataclass(frozen=True)
class LiveDisclosureSpecification(DisclosureSpecification):
    """
    Disclosure specification that uses the current time to determine if disclosure should occur.

    This object will create a new datetime object each time it is called, so it will always use the current time.
    """
    _disclosure_specification_provider: Callable[[], DisclosureSpecification] = field(
        default=lambda: _FixedTimeDisclosureSpecification()
    )

    def is_email_disclosure_deadline_met(self, contact_date: datetime) -> bool:
        return self._disclosure_specification_provider().is_email_disclosure_deadline_met(contact_date)

    def is_issue_pmpvr_request_deadline_met(self, contact_date: datetime) -> bool:
        return self._disclosure_specification_provider().is_issue_pmpvr_request_deadline_met(contact_date)


@dataclass(frozen=True)
class _FixedTimeDisclosureSpecification(DisclosureSpecification):
    """
    Disclosure specification that uses the current time to determine if disclosure should occur.
    This object is frozen to the time it was created. This is great for testing, but not good to use directly in
    production where the time will change in a system that is running for multiple days.
    """
    now: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))

    def __post_init__(self):
        self._validate_datetime_has_tzinfo("now", self.now)

    def _is_weekend(self) -> bool:
        return self.now.weekday() in (5, 6)

    def is_email_disclosure_deadline_met(self, contact_date: datetime) -> bool:
        self._validate_datetime_has_tzinfo("contact_date", contact_date)
        if self._is_weekend():
            # It's a weekend, don't disclose
            return False
        if (self.now - contact_date).days > 90:
            return True
        return False

    def is_issue_pmpvr_request_deadline_met(self, contact_date: datetime) -> bool:
        self._validate_datetime_has_tzinfo("contact_date", contact_date)
        if self._is_weekend():
            # It's a weekend, don't disclose
            return False
        if (self.now - contact_date).days > 35:
            return True
        return False

    @staticmethod
    def _validate_datetime_has_tzinfo(name: str, value: datetime):
        if value.tzinfo is None:
            raise ValueError(f"{name} must have a timezone")
