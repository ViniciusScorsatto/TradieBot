# Support Knowledge Base Workflow

The bug-triage assistant uses curated markdown files from [`/docs/support-kb/bugs`](/Users/viniciusscorsatto/Desktop/AI%20Projects/Nz%20Fuel/docs/support-kb/bugs).

## How to update it

1. Add or edit markdown files in `docs/support-kb/bugs/`
2. Run:

```bash
python3 scripts/sync_support_kb.py
```

3. Copy the printed vector store ID into Railway:

```env
OPENAI_SUPPORT_VECTOR_STORE_ID=vs_...
```

## Article format

Use the structure documented in [`/docs/support-kb/bugs/README.md`](/Users/viniciusscorsatto/Desktop/AI%20Projects/Nz%20Fuel/docs/support-kb/bugs/README.md).

Keep entries:
- short
- factual
- reviewed
- limited to product troubleshooting, not policy or legal advice
