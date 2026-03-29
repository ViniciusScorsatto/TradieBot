# Title
Voice note was not transcribed or was parsed incorrectly

# Symptom
The user says a voice note failed to transcribe, failed to become line items, or combined multiple items incorrectly.

# Likely causes
- The voice note is too long.
- The user is not currently in an active `/invoice` draft.
- The wording is too unclear or mixes items in a way the parser cannot split.
- Free or paid voice allowance has been exhausted.

# Troubleshooting steps
1. Ask the user to start with `/invoice` before sending the voice note.
2. Remind them the voice note must be 60 seconds or shorter.
3. Suggest a clearer phrasing such as `Wood 45. Service 100. Materials 45.`
4. If the voice limit was reached, tell them they can keep going with text or unlock more voice minutes.

# Escalation guidance
Escalate if short, clear voice notes in an active invoice draft still fail repeatedly.

# Do not answer if
- The user is asking for refunds or billing changes.
- The issue is really about OpenAI pricing or legal/compliance advice.
