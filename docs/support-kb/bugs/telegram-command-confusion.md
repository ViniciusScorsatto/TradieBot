# Title
Telegram command is not behaving as expected

# Symptom
The user says `/start`, `/invoice`, `/clients`, `/profile`, or another command did not do what they expected.

# Likely causes
- The user is not in the right mode for that action.
- The command menu has not refreshed yet.
- The user expected a follow-up action that belongs to a different command.

# Troubleshooting steps
1. Ask the user to send the command again directly in the chat.
2. For command menu issues, ask them to send `/start` and reopen the slash-command list.
3. If they are working on an invoice, remind them that `/invoice` starts the draft and `/generate` finishes it.
4. If they need saved client or business details, direct them to `/clients` or `/profile`.

# Escalation guidance
Escalate if a command consistently fails or does nothing after retrying.

# Do not answer if
- The issue is about billing or account ownership.
- The user is reporting a deployment/admin-only problem.
