# Title
Payment succeeded but credits did not unlock

# Symptom
The user says they paid in Stripe but invoice credits or voice minutes did not appear in the bot.

# Likely causes
- The webhook has not been processed yet.
- The user returned to Telegram before the webhook finished.
- The checkout session was completed for a different Telegram account.

# Troubleshooting steps
1. Ask the user to return to Telegram and try the action again after a short wait.
2. Ask them whether they completed checkout from the same Telegram account that opened the payment link.
3. If they bought invoice credits, ask them to try creating or generating an invoice again.
4. If they bought voice minutes, ask them to try sending a voice note again.

# Escalation guidance
Escalate if payment is confirmed and the credits still do not appear after retrying in Telegram.

# Do not answer if
- The user is asking for refunds or chargebacks.
- The issue needs financial/account reconciliation beyond a simple retry.
