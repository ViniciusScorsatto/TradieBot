# InvoiceBot Retention Policy

This is the operational retention baseline for InvoiceBot. It is a practical product policy, not legal advice.

## Retention table

| Data type | Retention | Reason | Cleanup action |
|---|---:|---|---|
| Active invoice drafts with no recent activity | 30 days | Drafts are useful short-term, but stale drafts are not essential long-term | Deleted automatically by daily cleanup job |
| Closed support tickets | 365 days | Keep enough support history for product debugging and customer follow-up | Deleted automatically by daily cleanup job |
| Promotion delivery logs | 90 days | Useful for short-term campaign troubleshooting and delivery auditing | Deleted automatically by daily cleanup job |
| Generated invoices | Until user deletion request or business-directed removal | Core customer record and product output | No automatic deletion in v1 |
| Clients | Until user deletion request or business-directed removal | Core user-managed business data | No automatic deletion in v1 |
| Business profiles | Until user deletion request or business-directed removal | Core account configuration | No automatic deletion in v1 |
| Stripe payment metadata | Until user deletion request or accounting/business-directed removal | Billing, reconciliation, and operational support | No automatic deletion in v1 |
| Voice transcript text shown in chat | Not stored as a separate database record | Only used inline in the bot flow | No retention beyond normal chat history |
| Raw uploaded voice files | Temporary only | Needed only for transcription request | Removed after processing by runtime temp-file handling |

## Automatic cleanup job

The existing daily Railway cron job now does two things:

1. On the first day of the month in `Pacific/Auckland`, reset free monthly invoice and voice usage counters
2. Every day, remove stale/non-essential records according to the retention windows above

Current environment variables:

```env
DRAFT_RETENTION_DAYS=30
CLOSED_TICKET_RETENTION_DAYS=365
PROMOTION_DELIVERY_RETENTION_DAYS=90
```

## Notes

- Only `CLOSED` support tickets are deleted automatically. Open and in-progress tickets are preserved.
- This policy should be reviewed before public launch and again once production usage patterns are clear.
- If legal review requires longer or shorter retention for any category, update both this document and the cron env values together.
