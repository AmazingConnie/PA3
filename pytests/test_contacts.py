import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import contacts  # noqa: E402
from contacts import ContactError  # noqa: E402


@pytest.fixture
def book(tmp_path):
    path = tmp_path / "contact_book.json"
    path.write_text("")  # starts empty, like the real file
    return str(path)


def read(book):
    with open(book) as f:
        return json.load(f)


# ---------- add ----------

def test_add_contact_with_all_fields(book):
    contacts.add_contact("Jane Doe", phone="555-0123", email="jane@example.com",
                         country="Canada", path=book)
    assert read(book) == [{"name": "Jane Doe", "phone": "555-0123",
                           "email": "jane@example.com", "country": "Canada"}]


def test_add_contact_name_only(book):
    contacts.add_contact("  Jane Doe  ", path=book)
    assert read(book) == [{"name": "Jane Doe"}]


@pytest.mark.parametrize("name", [None, "", "   "])
def test_add_rejects_blank_name(book, name):
    with pytest.raises(ContactError):
        contacts.add_contact(name, path=book)
    assert contacts.load_contacts(book) == []


def test_add_rejects_bad_email(book):
    with pytest.raises(ContactError):
        contacts.add_contact("Jane", email="not-an-email", path=book)


@pytest.mark.parametrize("phone", ["123", "555-0123 x123", "1234567890123456", "12+34567"])
def test_add_rejects_bad_phone(book, phone):
    with pytest.raises(ContactError):
        contacts.add_contact("Jane", phone=phone, path=book)


@pytest.mark.parametrize("phone", ["555-0123", "+1 (555) 012.3456", "5550123"])
def test_add_accepts_good_phone(book, phone):
    contacts.add_contact("Jane", phone=phone, path=book)
    assert read(book)[0]["phone"] == phone


def test_add_duplicate_rejected_when_user_declines(book):
    contacts.add_contact("Jane Doe", path=book)
    with pytest.raises(ContactError):
        contacts.add_contact(" jane doe ", path=book, ask=lambda _: "n")
    assert len(read(book)) == 1


def test_add_duplicate_gets_number_when_user_accepts(book):
    contacts.add_contact("Jane Doe", path=book)
    contacts.add_contact("Jane Doe", path=book, ask=lambda _: "y")
    contacts.add_contact("Jane Doe", path=book, ask=lambda _: "y")
    assert [c["name"] for c in read(book)] == ["Jane Doe", "Jane Doe 2", "Jane Doe 3"]


# ---------- update ----------

def test_update_phone(book):
    contacts.add_contact("Jane Doe", phone="555-0123", path=book)
    contacts.update_contact("jane doe", phone="555-6720", path=book)
    assert read(book)[0]["phone"] == "555-6720"


def test_update_new_name(book):
    contacts.add_contact("Jane Doe", path=book)
    contacts.update_contact("Jane Doe", new_name="Jane Smith", path=book)
    assert read(book)[0]["name"] == "Jane Smith"


def test_update_blank_value_removes_field(book):
    contacts.add_contact("Jane Doe", country="Canada", path=book)
    contacts.update_contact("Jane Doe", country="", path=book)
    assert "country" not in read(book)[0]


def test_update_rejects_existing_name(book):
    contacts.add_contact("Jane Doe", path=book)
    contacts.add_contact("John Roe", path=book)
    with pytest.raises(ContactError):
        contacts.update_contact("John Roe", new_name="JANE DOE", path=book)


def test_update_allows_changing_case_of_own_name(book):
    contacts.add_contact("jane doe", path=book)
    contacts.update_contact("Jane Doe", new_name="Jane Doe", path=book)
    assert read(book)[0]["name"] == "Jane Doe"


def test_update_requires_whole_name(book):
    contacts.add_contact("Jane Doe", path=book)
    with pytest.raises(ContactError):
        contacts.update_contact("Jane", phone="555-6720", path=book)


def test_update_rejects_bad_email(book):
    contacts.add_contact("Jane Doe", path=book)
    with pytest.raises(ContactError):
        contacts.update_contact("Jane Doe", email="bad", path=book)
    assert "email" not in read(book)[0]


# ---------- delete ----------

def test_delete_with_confirmation(book):
    contacts.add_contact("Jane Doe", path=book)
    contacts.delete_contact("JANE DOE", path=book, ask=lambda _: "y")
    assert read(book) == []


def test_delete_cancelled(book):
    contacts.add_contact("Jane Doe", path=book)
    assert contacts.delete_contact("Jane Doe", path=book, ask=lambda _: "n") is None
    assert len(read(book)) == 1


def test_delete_skip_confirmation(book):
    contacts.add_contact("Jane Doe", path=book)

    def fail(_):
        raise AssertionError("should not ask")

    contacts.delete_contact("Jane Doe", path=book, confirm=False, ask=fail)
    assert read(book) == []


def test_delete_requires_whole_name(book):
    contacts.add_contact("Jane Doe", path=book)
    with pytest.raises(ContactError):
        contacts.delete_contact("Jane", path=book, confirm=False)


# ---------- query ----------

def test_list_contacts(book):
    assert contacts.list_contacts(book) == []
    contacts.add_contact("Jane Doe", path=book)
    contacts.add_contact("John Roe", path=book)
    assert [c["name"] for c in contacts.list_contacts(book)] == ["Jane Doe", "John Roe"]


def test_search_by_name_ignores_case(book):
    contacts.add_contact("Jane Doe", path=book)
    contacts.add_contact("John Roe", path=book)
    assert [c["name"] for c in contacts.search_contacts(name="JANE", path=book)] == ["Jane Doe"]


def test_search_by_email_and_phone(book):
    contacts.add_contact("Jane Doe", phone="555-9999", email="jane@example.com", path=book)
    contacts.add_contact("John Roe", phone="555-0000", email="john@example.org", path=book)
    assert [c["name"] for c in contacts.search_contacts(email="example.com", path=book)] == ["Jane Doe"]
    assert [c["name"] for c in contacts.search_contacts(phone="9999", path=book)] == ["Jane Doe"]


def test_search_requires_criteria(book):
    with pytest.raises(ContactError):
        contacts.search_contacts(path=book)


# ---------- backup and command line ----------

def test_backup_restored_when_write_fails(book, monkeypatch):
    contacts.add_contact("Jane Doe", path=book)

    def broken_dump(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(contacts.json, "dump", broken_dump)
    with pytest.raises(OSError):
        contacts.add_contact("John Roe", path=book)
    monkeypatch.undo()
    assert read(book) == [{"name": "Jane Doe"}]
    assert os.path.exists(book + ".bak")


def test_cli_rejects_combined_modes(book):
    with pytest.raises(SystemExit):
        contacts.main(["--list", "--delete", "Jane Doe"], path=book)
    with pytest.raises(SystemExit):
        contacts.main(["--search", "--update", "Jane Doe"], path=book)


def test_cli_add_update_search_delete(book, capsys):
    assert contacts.main(["Jane Doe", "--phone", "555-0123", "--email", "jane@example.com",
                          "--country", "Canada"], path=book) == 0
    assert contacts.main(["--update", "Jane Doe", "--phone", "555-6720"], path=book) == 0
    assert contacts.main(["--search", "--name", "jane"], path=book) == 0
    assert "555-6720" in capsys.readouterr().out
    assert contacts.main(["--delete", "Jane Doe", "--yes"], path=book) == 0
    assert read(book) == []


def test_cli_reports_error_for_bad_input(book, capsys):
    assert contacts.main(["Jane Doe", "--email", "bad"], path=book) == 1
    assert "Error" in capsys.readouterr().err
