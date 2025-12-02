# test_email_system.py

import datetime
import os
import tempfile
from email_system import (
    Email,
    EmailAddress,
    EmailService,
    LoggingEmailService,
    Status,
)


def test_email_address():
    """Тестирование класса EmailAddress"""
    # Нормализация
    addr = EmailAddress("  Aleks@Example.COM  ")
    assert addr.address == "aleks@example.com"

    # Маскирование
    assert addr.masked == "al***@example.com"

    # Валидация
    try:
        EmailAddress("invalid")
        assert False, "Должна быть ошибка валидации"
    except ValueError:
        pass

    try:
        EmailAddress("test@example.org")
        assert False, "Должна быть ошибка домена"
    except ValueError:
        pass

    print("✓ EmailAddress тесты пройдены")


def test_email_preparation():
    """Тестирование подготовки письма"""
    sender = EmailAddress("sender@example.com")
    recipient = EmailAddress("recipient@example.ru")

    # Письмо с валидными данными
    email = Email(
        subject="  Тема  ",
        body="  Первая строка  \n  Вторая строка  ",
        sender=sender,
        recipients=recipient,
    )

    email.prepare()

    assert email.subject == "Тема"
    assert email.body == "Первая строка Вторая строка"
    assert email.status == Status.READY
    assert len(email.short_body) <= 50

    # Письмо с невалидными данными
    invalid_email = Email(
        subject="",
        body="Текст",
        sender=sender,
        recipients=recipient,
    )
    invalid_email.prepare()
    assert invalid_email.status == Status.INVALID

    print("✓ Email подготовка тесты пройдены")


def test_email_service():
    """Тестирование сервиса отправки"""
    sender = EmailAddress("sender@example.com")
    recipient1 = EmailAddress("r1@example.com")
    recipient2 = EmailAddress("r2@example.ru")

    email = Email(
        subject="Тест",
        body="Тело письма",
        sender=sender,
        recipients=[recipient1, recipient2],
    )
    email.prepare()

    original_status = email.status
    original_date = email.date

    service = EmailService()
    sent_emails = service.send_email(email)

    # Проверяем что исходное письмо не изменилось
    assert email.status == original_status
    assert email.date == original_date

    # Проверяем отправленные копии
    assert len(sent_emails) == 2
    assert all(e.status == Status.SENT for e in sent_emails)
    assert sent_emails[0].recipients == [recipient1]
    assert sent_emails[1].recipients == [recipient2]
    assert sent_emails[0].date != sent_emails[1].date

    # Проверяем отправку неподготовленного письма
    draft_email = Email(
        subject="Черновик",
        body="",
        sender=sender,
        recipients=recipient1,
    )
    draft_sent = service.send_email(draft_email)
    assert draft_sent[0].status == Status.FAILED

    print("✓ EmailService тесты пройдены")


def test_logging_service():
    """Тестирование логирующего сервиса"""
    # Используем временный файл для логов
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_file = f.name

    try:
        sender = EmailAddress("logger@example.com")
        recipient = EmailAddress("log_recipient@example.net")

        email = Email(
            subject="Тестовое логирование",
            body="Сообщение для лога",
            sender=sender,
            recipients=recipient,
        )
        email.prepare()

        service = LoggingEmailService(log_file=log_file)
        sent_emails = service.send_email(email)

        # Проверяем что лог файл создан и содержит запись
        assert os.path.exists(log_file)
        with open(log_file, 'r') as f:
            log_content = f.read()
            assert "Email sent from" in log_content
            assert "logger@example.com" in log_content
            assert "log_recipient@example.net" in log_content

        print("✓ LoggingEmailService тесты пройдены")
    finally:
        if os.path.exists(log_file):
            os.remove(log_file)


def test_edge_cases():
    """Тестирование граничных случаев"""
    # Один получатель как объект, а не список
    sender = EmailAddress("edge@example.com")
    recipient = EmailAddress("single@example.ru")

    email = Email(
        subject="Тест",
        body="Тест",
        sender=sender,
        recipients=recipient,  # Один объект, не список
    )
    assert isinstance(email.recipients, list)
    assert len(email.recipients) == 1

    # Очень длинное тело
    long_body = "A" * 100
    email2 = Email(
        subject="Длинное",
        body=long_body,
        sender=sender,
        recipients=recipient,
    )
    email2.prepare()
    assert len(email2.short_body) == 50
    assert email2.short_body.endswith("...")

    # Тело ровно 50 символов
    exact_body = "B" * 50
    email3 = Email(
        subject="Точное",
        body=exact_body,
        sender=sender,
        recipients=recipient,
    )
    email3.prepare()
    assert len(email3.short_body) == 50
    assert not email3.short_body.endswith("...")

    print("✓ Граничные случаи тесты пройдены")


def run_all_tests():
    """Запуск всех тестов"""
    print("Запуск тестов email системы...\n")

    test_email_address()
    test_email_preparation()
    test_email_service()
    test_logging_service()
    test_edge_cases()

    print("\n✅ Все тесты успешно пройдены!")


if __name__ == "__main__":
    run_all_tests()