# Rules
- **Name is Required**: If name is missing or left blank, raise an error to flag it down and reject it. This blocks the user from uploading an improper entry to the JSON file. 
-- **Whole name is Required for Update or Delete**: `--update` and `--delete` need the contact's whole name (case doesn't matter). Use `--search` first if you're not sure of it.
- **Names are Unique**, ignoring case and surrounding spaces. If you add a name that already exists in the contact list, the program will reject it. If you try to update an existing contact with a name that already exists in the contact book, the program will reject it. 
- **Email** must look like the format `name@example.com`, otherwise the program will reject it
- **Phone** may contain digits, spaces, dashes, dots, parentheses and a leading `+`, with
  7 to 15 digits in total. Extensions such as `x123` aren't accepted.
- **Combining Functions is Prohibited**: `--search`, `--list`, `--update` and `--delete` can't be combined with each other.
- **Make a backup**: Make a backup in case a valid write to the JSON file fails.