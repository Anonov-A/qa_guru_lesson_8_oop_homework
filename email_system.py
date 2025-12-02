from __future__ import annotations

import copy
import datetime
import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import List, Union


class Status(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    SENT = "sent"
    FAILED = "failed"
    INVALID = "invalid"


class EmailAddress:
    VALID_DOMAINS = (".com", ".ru", ".net")

    def __init__(self, address: str):
        self._address = self._normalize(address)
        self._validate()

    @property
    def address(self) -> str:
        return self._address

    @property
    def masked(self) -> str:
        local_part, domain = self._address.split("@")
        masked_local = local_part[:2] + "***"
        return f"{masked_local}@{domain}"

    def _normalize(self, address: str) -> str:
        return address.strip().lower()

    def _validate(self) -> None:
        if "@" not in self._address:
            raise ValueError("Email address must contain '@'")

        if not any(self._address.endswith(domain) for domain in self.VALID_DOMAINS):
            raise ValueError(f"Domain must end with {self.VALID_DOMAINS}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EmailAddress):
            return NotImplemented
        return self._address == other._address

    def __hash__(self) -> int:
        return hash(self._address)

    def __repr__(self) -> str:
        return self.masked

    def __str__(self) -> str:
        return self._address


@dataclass
class Email:
    subject: str
    body: str
    sender: EmailAddress
    recipients: Union[EmailAddress, List[EmailAddress]]
    date: datetime.datetime = field(default_factory=datetime.datetime.now)
    short_body: str = field(default="", init=False)
    status: Status = field(default=Status.DRAFT, init=False)

    def __post_init__(self) -> None:
        if isinstance(self.recipients, EmailAddress):
            self.recipients = [self.recipients]
        elif isinstance(self.recipients, list):
            self.recipients = list(self.recipients)
        else:
            raise TypeError("Recipients must be EmailAddress or list of EmailAddress")

    def _clean_text(self, text: str) -> str:
        lines = (line.strip() for line in text.split("\n"))
        return " ".join(line for line in lines if line)

    def _add_short_body(self) -> None:
        if not self.body:
            self.short_body = ""
            return

        cleaned_body = self._clean_text(self.body)
        if len(cleaned_body) <= 50:
            self.short_body = cleaned_body
        else:
            self.short_body = cleaned_body[:47] + "..."

    def prepare(self) -> None:
        self.subject = self._clean_text(self.subject)
        self.body = self._clean_text(self.body)

        self._add_short_body()

        if (
            self.subject
            and self.body
            and self.sender
            and self.recipients
            and all(isinstance(r, EmailAddress) for r in self.recipients)
        ):
            self.status = Status.READY
        else:
            self.status = Status.INVALID

    def __repr__(self) -> str:
        recipients_str = ", ".join(str(recipient.masked) for recipient in self.recipients)
        return (
            f"Email(subject='{self.subject}', sender={self.sender.masked}, "
            f"recipients=[{recipients_str}], status={self.status})"
        )


class EmailService:
    def send_email(self, email: Email) -> List[Email]:
        sent_emails = []

        for recipient in email.recipients:
            email_copy = copy.deepcopy(email)
            email_copy.recipients = [recipient]
            email_copy.date = datetime.datetime.now()

            if email_copy.status == Status.READY:
                email_copy.status = Status.SENT
            else:
                email_copy.status = Status.FAILED

            sent_emails.append(email_copy)

        return sent_emails


class LoggingEmailService(EmailService):
    def __init__(self, log_file: str = "send.log"):
        super().__init__()
        self.log_file = log_file
        self._setup_logging()

    def _setup_logging(self) -> None:
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def send_email(self, email: Email) -> List[Email]:
        sent_emails = super().send_email(email)

        for sent_email in sent_emails:
            log_message = (
                f"Email sent from {sent_email.sender.address} to "
                f"{sent_email.recipients[0].address}. "
                f"Subject: {sent_email.subject}. "
                f"Status: {sent_email.status}"
            )
            logging.info(log_message)

        return sent_emails