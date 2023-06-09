import datetime
import unittest

from parameterized import parameterized

# noinspection PyProtectedMember
from open_auto_vuln_disclose.common.timeline import _FixedTimeDisclosureSpecification, LiveDisclosureSpecification


class DisclosureSpecificationTest(unittest.TestCase):
    DISCLOSURE_SUNDAY = datetime.datetime(2020, 1, 5, tzinfo=datetime.timezone.utc)
    DISCLOSURE_MONDAY = DISCLOSURE_SUNDAY + datetime.timedelta(days=1)
    DISCLOSURE_TUESDAY = DISCLOSURE_SUNDAY + datetime.timedelta(days=2)
    DISCLOSURE_WEDNESDAY = DISCLOSURE_SUNDAY + datetime.timedelta(days=3)
    DISCLOSURE_THURSDAY = DISCLOSURE_SUNDAY + datetime.timedelta(days=4)
    DISCLOSURE_FRIDAY = DISCLOSURE_SUNDAY + datetime.timedelta(days=5)
    DISCLOSURE_SATURDAY = DISCLOSURE_SUNDAY + datetime.timedelta(days=6)

    def test_fails_when_created_without_timezone(self):
        # Then a ValueError is raised
        with self.assertRaises(ValueError):
            # Given a disclosure manager without a timezone
            _FixedTimeDisclosureSpecification(now=datetime.datetime(2020, 1, 5))

    def test_fails_when_passed_date_without_timezone(self):
        # Given a default Disclosure Manager, which has a timezone
        spec = _FixedTimeDisclosureSpecification()
        # Then a ValueError is raised
        # When a date without a timezone is passed
        with self.assertRaises(ValueError):
            spec.is_email_disclosure_deadline_met(datetime.datetime(2020, 1, 5))
        with self.assertRaises(ValueError):
            spec.is_issue_pmpvr_request_deadline_met(datetime.datetime(2020, 1, 5))

    @parameterized.expand([
        ("SATURDAY", DISCLOSURE_SATURDAY,),
        ("SUNDAY", DISCLOSURE_SUNDAY,),
    ])
    def test_today_is_weekend(self, _, today: datetime.datetime):
        # Given a disclosure manager with 'now' as a weekend
        spec = _FixedTimeDisclosureSpecification(now=today)
        # Then
        self.assertFalse(
            spec.is_email_disclosure_deadline_met(today),
            "Disclosure on same day is not allowed"
        )
        self.assertFalse(
            spec.is_issue_pmpvr_request_deadline_met(today),
            "PMPVR request completion on same day is not allowed"
        )
        self.assertFalse(
            spec.is_email_disclosure_deadline_met(today - datetime.timedelta(days=180)),
            "Disclosure of an email sent 180 days previous is still not allowed when today is a weekend"
        )
        self.assertFalse(
            spec.is_issue_pmpvr_request_deadline_met(today - datetime.timedelta(days=180)),
            "PMPVR request completion of an issue opened 180 days previous is still not allowed when today is a weekend"
        )

    @parameterized.expand([
        ("MONDAY", DISCLOSURE_MONDAY,),
        ("TUESDAY", DISCLOSURE_TUESDAY,),
        ("WEDNESDAY", DISCLOSURE_WEDNESDAY,),
        ("THURSDAY", DISCLOSURE_THURSDAY,),
        ("FRIDAY", DISCLOSURE_FRIDAY,),
    ])
    def test_today_is_weekday(self, _, today: datetime.datetime):
        # Given a disclosure manager with 'now' as a weekday
        spec = _FixedTimeDisclosureSpecification(now=today)
        # Then
        self.assertFalse(
            spec.is_email_disclosure_deadline_met(today),
            "Disclosure on same day is not allowed"
        )
        self.assertFalse(
            spec.is_issue_pmpvr_request_deadline_met(today),
            "PMPVR request completion on same day is not allowed"
        )
        self.assertTrue(
            spec.is_email_disclosure_deadline_met(
                today - datetime.timedelta(days=180)
            ),
            "Disclosure of an email sent 180 days previous is allowed"
        )
        self.assertTrue(
            spec.is_issue_pmpvr_request_deadline_met(
                today - datetime.timedelta(days=180)
            ),
            "PMPVR request completion of an issue opened 180 days previous is allowed"
        )
        self.assertTrue(
            spec.is_email_disclosure_deadline_met(
                today - datetime.timedelta(days=91)
            ),
            "Disclosure of an email sent 91 days previous is allowed"
        )
        self.assertTrue(
            spec.is_issue_pmpvr_request_deadline_met(
                today - datetime.timedelta(days=36)
            ),
            "PMPVR request completion of an issue opened 36 days previous is allowed"
        )
        self.assertFalse(
            spec.is_email_disclosure_deadline_met(
                today - datetime.timedelta(days=90)
            ),
            "Disclosure of an email sent exactly 90 days previous is not allowed"
        )
        self.assertFalse(
            spec.is_issue_pmpvr_request_deadline_met(
                today - datetime.timedelta(days=35)
            ),
            "PMPVR request completion of an issue opened exactly 35 days previous is not allowed"
        )

    def test_day_change(self):
        # Given a disclosure manager that tracks the current time live
        # When the current day is Sunday
        current_day = self.DISCLOSURE_SUNDAY
        # And the contact date was 91 days ago
        contact_date = current_day - datetime.timedelta(days=91)
        spec = LiveDisclosureSpecification(lambda: _FixedTimeDisclosureSpecification(now=current_day))
        # Then
        self.assertFalse(
            spec.is_email_disclosure_deadline_met(contact_date),
            "Disclosure of an email sent 91 days previous is not allowed on a weekend"
        )
        self.assertFalse(
            spec.is_issue_pmpvr_request_deadline_met(contact_date),
            "PMPVR request completion of an issue opened 91 days previous is not allowed on a weekend"
        )
        # When the current day is Monday
        current_day = self.DISCLOSURE_MONDAY
        # Then
        self.assertTrue(
            spec.is_email_disclosure_deadline_met(contact_date),
            "Disclosure of an email sent 91 days previous is allowed on a weekday"
        )
        self.assertTrue(
            spec.is_issue_pmpvr_request_deadline_met(contact_date),
            "PMPVR request completion of an issue opened 91 days previous is allowed on a weekday"
        )


if __name__ == '__main__':
    unittest.main()
