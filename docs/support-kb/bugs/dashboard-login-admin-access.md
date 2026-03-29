# Title
Dashboard login or admin access issue

# Symptom
The user says they cannot sign in to the dashboard, cannot see admin pages, or are being redirected unexpectedly.

# Likely causes
- Admin credentials or TOTP code are wrong.
- The user is signed out.
- The account is not meant to access the private admin dashboard.

# Troubleshooting steps
1. Ask the user to retry login with the correct admin email and password.
2. If TOTP is enabled, ask them to use a fresh authenticator code.
3. If they were signed out, ask them to log in again and reopen the dashboard page.

# Escalation guidance
Escalate if a valid admin still cannot log in or if access looks locked unexpectedly.

# Do not answer if
- The user needs password resets, account ownership changes, or security exceptions.
- The issue could involve compromised access or security incidents.
