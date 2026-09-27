# Rules
- **Names are unique**, ignoring case and surrounding spaces. Adding or renaming to a name
  that already exists is refused.
- `--update` and `--delete` need the contact's whole name (case doesn't matter). Use
  `--search` first if you're not sure of it.
- **Email** must look like `name@example.com`. It isn't checked beyond its format.
- **Phone** may contain digits, spaces, dashes, dots, parentheses and a leading `+`, with
  7 to 15 digits in total. Extensions such as `x123` aren't accepted.
- `--search`, `--list`, `--update` and `--delete` can't be combined with each other.

# Examples

# Add an entry 
```bash
# add a contact; prompts for each required field; reject if at least one required field is blank
python3 contacts.py   

# add with name (required)
python3 contacts.py "Jane Doe"   

# add with optional fields such as phone, email, and country
python3 contacts.py "Jane Doe" --phone 555-0123 --email jane@example.com  --country Canada 

# if contact already exists, ask if it wants to add a number to the name of the new, duplicate contact
python3 contacts.py "Jane Doe" --phone 555-0123 --email jane@example.com  --country Canada 

```

# Search an entry 
```bash
python3 contacts.py --list                            # show every contact
python3 contacts.py --search --name "jane"            # names containing "jane" (ignores case)
python3 contacts.py --search --email "555-9999"            # names containing "978" (ignores case)
```

# Update an entry
```bash
python3 contacts.py --update "Jane Doe" --phone "555-6720"
python3 contacts.py --update "Jane Doe" --new-name "Jane Smith"
python3 contacts.py --update "Jane Doe" --country ""  # a blank value removes the field
```

# Delete an entry
```bash
python3 contacts.py --delete "Jane Doe"               # asks for confirmation
python3 contacts.py --delete "Jane Doe" --yes         # skips the question
```