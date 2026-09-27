# Contact Book

A simple command-line contact book. `contacts.py` runs the commands and stores contacts in
`contact_book.json`.

Requires Python 3. No extra packages are needed to run it; the tests need `pytest`.

## Usage

### Add a contact

```bash
python3 contacts.py                      # asks for the name
python3 contacts.py "Jane Doe"
python3 contacts.py "Jane Doe" --phone 555-0123 --email jane@example.com --country Canada
```

If a contact with that name already exists, you're asked whether to save the new one with a
number added (for example `Jane Doe 2`). Otherwise it's rejected.

### List and search

```bash
python3 contacts.py --list                     # show every contact
python3 contacts.py --search --name "jane"     # names containing "jane"
python3 contacts.py --search --phone "555"     # also works with --email and --country
```

Searches match part of a field and ignore case.

### Update a contact

```bash
python3 contacts.py --update "Jane Doe" --phone 555-6720
python3 contacts.py --update "Jane Doe" --new-name "Jane Smith"
python3 contacts.py --update "Jane Doe" --country ""    # a blank value removes the field
```

### Delete a contact

```bash
python3 contacts.py --delete "Jane Doe"          # asks for confirmation
python3 contacts.py --delete "Jane Doe" --yes    # skips the question
```

## Rules

- **Name is required** and can't be blank.
- **Names are unique**, ignoring case and surrounding spaces. Adding or renaming to a name
  that already exists is rejected.
- `--update` and `--delete` need the contact's **whole name** (case doesn't matter). Use
  `--search` first if you're not sure of it.
- **Email** must look like `name@example.com`.
- **Phone** may contain digits, spaces, dashes, dots, parentheses and a leading `+`, with
  7 to 15 digits in total. Extensions such as `x123` aren't accepted.
- `--list`, `--search`, `--update` and `--delete` can't be combined.
- Before each save, the current book is copied to `contact_book.json.bak`. If the write
  fails, the backup is restored.

The full rules and examples are in `rules.md` and `conventions.md`.

## Running the tests

```bash
python3 -m pytest pytests/test_contacts.py
```

The tests use a temporary contact book, so they don't change `contact_book.json`.

## Files

| File | Purpose |
| --- | --- |
| `contacts.py` | The contact book commands |
| `contact_book.json` | Where contacts are stored |
| `pytests/test_contacts.py` | Tests for each command |
| `rules.md` | Rules each command follows |
| `conventions.md` | Example commands |
