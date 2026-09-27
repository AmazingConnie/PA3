"""A simple command-line contact book backed by contact_book.json."""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile

BOOK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contact_book.json")
OPTIONAL_FIELDS = ("phone", "email", "country")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_CHARS_RE = re.compile(r"^\+?[0-9 .\-()]+$")


class ContactError(ValueError):
    """Raised when a contact operation is rejected."""


# ---------- storage ----------

def load_contacts(path=BOOK_PATH):
    """Return the list of contacts; a missing or empty file is an empty book."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ContactError(f"{path} does not contain a list of contacts")
    return data


def save_contacts(contacts, path=BOOK_PATH):
    """Write contacts to disk, keeping a backup and restoring it if the write fails."""
    backup = path + ".bak"
    if os.path.exists(path):
        shutil.copy2(path, backup)
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(contacts, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        if os.path.exists(backup):
            shutil.copy2(backup, path)
        raise


# ---------- validation ----------

def normalize_name(name):
    return name.strip().casefold()


def validate_name(name):
    if name is None or not name.strip():
        raise ContactError("Name is required and cannot be blank.")
    return name.strip()


def validate_email(email):
    if not EMAIL_RE.match(email):
        raise ContactError(f"Invalid email {email!r}; expected something like name@example.com.")
    return email


def validate_phone(phone):
    digits = sum(c.isdigit() for c in phone)
    if not PHONE_CHARS_RE.match(phone) or not 7 <= digits <= 15:
        raise ContactError(
            f"Invalid phone {phone!r}; use digits, spaces, dashes, dots, parentheses "
            "and an optional leading +, with 7 to 15 digits."
        )
    return phone


def validate_fields(fields):
    """Validate optional fields; blank values are kept as '' (meaning 'remove' on update)."""
    cleaned = {}
    for key, value in fields.items():
        if value is None:
            continue
        value = value.strip()
        if value:
            if key == "email":
                validate_email(value)
            elif key == "phone":
                validate_phone(value)
        cleaned[key] = value
    return cleaned


def find_contact(contacts, name):
    """Return the index of the contact whose whole name matches (ignoring case), or None."""
    target = normalize_name(name)
    for i, contact in enumerate(contacts):
        if normalize_name(contact["name"]) == target:
            return i
    return None


def next_free_name(contacts, name):
    """Return name with the smallest number suffix that isn't taken, e.g. 'Jane Doe 2'."""
    n = 2
    while find_contact(contacts, f"{name} {n}") is not None:
        n += 1
    return f"{name} {n}"


# ---------- operations ----------

def add_contact(name, phone=None, email=None, country=None, path=BOOK_PATH, ask=input):
    """Add a contact. If the name exists, offer to add a number to the new name; otherwise reject."""
    name = validate_name(name)
    fields = {k: v for k, v in validate_fields(
        {"phone": phone, "email": email, "country": country}).items() if v}
    contacts = load_contacts(path)

    if find_contact(contacts, name) is not None:
        suggestion = next_free_name(contacts, name)
        answer = ask(f"A contact named {name!r} already exists. Add as {suggestion!r} instead? [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            raise ContactError(f"A contact named {name!r} already exists.")
        name = suggestion

    contact = {"name": name, **fields}
    contacts.append(contact)
    save_contacts(contacts, path)
    return contact


def update_contact(name, new_name=None, phone=None, email=None, country=None, path=BOOK_PATH):
    """Update a contact found by its whole name. A blank field value removes that field."""
    name = validate_name(name)
    contacts = load_contacts(path)
    index = find_contact(contacts, name)
    if index is None:
        raise ContactError(f"No contact named {name!r}. Use --search to find the whole name.")

    fields = validate_fields({"phone": phone, "email": email, "country": country})
    if new_name is None and not fields:
        raise ContactError("Nothing to update; give --new-name, --phone, --email or --country.")

    contact = dict(contacts[index])
    if new_name is not None:
        new_name = validate_name(new_name)
        other = find_contact(contacts, new_name)
        if other is not None and other != index:
            raise ContactError(f"A contact named {new_name!r} already exists.")
        contact["name"] = new_name
    for key, value in fields.items():
        if value:
            contact[key] = value
        else:
            contact.pop(key, None)

    contacts[index] = contact
    save_contacts(contacts, path)
    return contact


def delete_contact(name, path=BOOK_PATH, confirm=True, ask=input):
    """Delete a contact found by its whole name, asking for confirmation unless confirm=False."""
    name = validate_name(name)
    contacts = load_contacts(path)
    index = find_contact(contacts, name)
    if index is None:
        raise ContactError(f"No contact named {name!r}. Use --search to find the whole name.")
    if confirm:
        answer = ask(f"Delete {contacts[index]['name']!r}? [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            return None
    removed = contacts.pop(index)
    save_contacts(contacts, path)
    return removed


def search_contacts(name=None, phone=None, email=None, country=None, path=BOOK_PATH):
    """Return contacts whose fields contain every given value (ignoring case)."""
    criteria = {k: v.strip().casefold() for k, v in
                {"name": name, "phone": phone, "email": email, "country": country}.items()
                if v is not None and v.strip()}
    if not criteria:
        raise ContactError("Give at least one of --name, --phone, --email or --country to search.")
    return [c for c in load_contacts(path)
            if all(value in c.get(key, "").casefold() for key, value in criteria.items())]


def list_contacts(path=BOOK_PATH):
    """Return every contact."""
    return load_contacts(path)


# ---------- command line ----------

def format_contact(contact):
    extras = ", ".join(f"{k}: {contact[k]}" for k in OPTIONAL_FIELDS if contact.get(k))
    return f"{contact['name']}" + (f" ({extras})" if extras else "")


def build_parser():
    parser = argparse.ArgumentParser(description="A simple contact book.")
    parser.add_argument("name", nargs="?", help="name of the contact to add")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--list", action="store_true", help="show every contact")
    mode.add_argument("--search", action="store_true", help="search contacts")
    mode.add_argument("--update", metavar="NAME", help="update the contact with this whole name")
    mode.add_argument("--delete", metavar="NAME", help="delete the contact with this whole name")
    parser.add_argument("--name", dest="search_name", help="name to search for")
    parser.add_argument("--new-name", help="new name when updating")
    parser.add_argument("--phone")
    parser.add_argument("--email")
    parser.add_argument("--country")
    parser.add_argument("--yes", action="store_true", help="skip the delete confirmation")
    return parser


def main(argv=None, path=BOOK_PATH):
    parser = build_parser()
    args = parser.parse_args(argv)
    fields = {"phone": args.phone, "email": args.email, "country": args.country}

    if args.name is not None and (args.list or args.search or args.update or args.delete):
        parser.error("a contact name can't be combined with --list, --search, --update or --delete")

    try:
        if args.list:
            contacts = list_contacts(path)
            for contact in contacts:
                print(format_contact(contact))
            if not contacts:
                print("The contact book is empty.")
        elif args.search:
            results = search_contacts(name=args.search_name, path=path, **fields)
            for contact in results:
                print(format_contact(contact))
            if not results:
                print("No matching contacts.")
        elif args.update is not None:
            contact = update_contact(args.update, new_name=args.new_name, path=path, **fields)
            print(f"Updated {format_contact(contact)}")
        elif args.delete is not None:
            removed = delete_contact(args.delete, path=path, confirm=not args.yes)
            print(f"Deleted {removed['name']}" if removed else "Nothing deleted.")
        else:
            name = args.name if args.name is not None else input("Name: ")
            contact = add_contact(name, path=path, **fields)
            print(f"Added {format_contact(contact)}")
    except (ContactError, json.JSONDecodeError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
