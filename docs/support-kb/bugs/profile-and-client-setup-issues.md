# Title
Business profile or client setup is incomplete

# Symptom
The user cannot generate an invoice correctly because company, GST, client, or payment details are missing.

# Likely causes
- Required profile fields were skipped.
- Client details are incomplete for a GST invoice.
- Payment details or logo were not added yet.

# Troubleshooting steps
1. Ask the user to run `/profile` and fill in business name and address first.
2. If they are GST registered, ask them to add the GST number in `/profile`.
3. Ask them to use `/newclient` or `/clients` to save the client before generating the invoice.
4. If they want bank details on the PDF, ask them to add payment details in `/profile`.

# Escalation guidance
Escalate if the user has already filled profile and client details but invoice checks still block them.

# Do not answer if
- The user is asking whether they legally need GST registration.
- The issue needs accounting, tax, or legal advice.
