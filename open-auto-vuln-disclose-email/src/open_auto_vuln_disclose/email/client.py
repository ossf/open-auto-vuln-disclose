from abc import ABC, abstractmethod
from typing import Union, Callable

from open_auto_vuln_disclose.common.email import EmailSendQueued, \
    AwaitingEmailResponses, EmailProcessingEndState
from open_auto_vuln_disclose.common.util import callable_not_implemented_exception


class EmailClient(ABC):
    @abstractmethod
    async def send_email(self, email_processing_step: EmailSendQueued) -> Union[
        EmailSendQueued, AwaitingEmailResponses
    ]:
        ...

    @abstractmethod
    async def check_for_email_responses(self, email_processing_step: AwaitingEmailResponses) -> Union[
        AwaitingEmailResponses, EmailProcessingEndState
    ]:
        ...

    @staticmethod
    def from_callable(
            send_email_response: Callable[[EmailSendQueued], Union[EmailSendQueued, AwaitingEmailResponses]],
            check_for_email_responses_response: Callable[
                [AwaitingEmailResponses],
                Union[AwaitingEmailResponses, EmailProcessingEndState]
            ],
    ):
        assert isinstance(send_email_response, Callable)
        assert isinstance(check_for_email_responses_response, Callable)

        class CallableEmailClient(EmailClient):

            async def send_email(self, email_processing_step: EmailSendQueued) -> Union[
                EmailSendQueued, AwaitingEmailResponses
            ]:
                return send_email_response(email_processing_step)

            async def check_for_email_responses(self, email_processing_step: AwaitingEmailResponses) -> Union[
                AwaitingEmailResponses, EmailProcessingEndState
            ]:
                return check_for_email_responses_response(email_processing_step)

        return CallableEmailClient()

    @staticmethod
    def from_callable_for_test(
            send_email_response: Callable[[EmailSendQueued], Union[EmailSendQueued, AwaitingEmailResponses]] =
            callable_not_implemented_exception("send_email was called unexpectedly"),
            check_for_email_responses_response: Callable[
                [AwaitingEmailResponses],
                Union[AwaitingEmailResponses, EmailProcessingEndState]
            ] = callable_not_implemented_exception("check_for_email_responses was called unexpectedly"),
    ):
        return EmailClient.from_callable(
            send_email_response=send_email_response,
            check_for_email_responses_response=check_for_email_responses_response,
        )

