# Title
Invoice generation fails or does not produce a PDF

# Symptom
The user says `/generate` does not work, the PDF does not arrive, or the bot says the invoice cannot be generated.

# Likely causes
- There are no items in the draft yet.
- Required business profile fields are missing.
- GST invoice validation is blocking generation because client information is incomplete.

# Troubleshooting steps
1. Ask the user to confirm they have started `/invoice` and added at least one item.
2. Ask them to run `/profile` and make sure business name and address are filled in.
3. If GST is enabled, ask them to select or create a client before trying `/generate` again.
4. For GST invoices over NZD 1,000, ask them to add at least one client identifier such as email, phone, address, or company.

# Escalation guidance
Escalate if the user has items in the draft, profile details are complete, and `/generate` still fails.

# Do not answer if
- The issue looks like billing, refunds, or legal/tax advice.
- The user is asking for account deletion, privacy, or admin access changes.
