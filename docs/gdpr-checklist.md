# InvoiceBot GDPR Checklist

This is the practical baseline checklist for getting InvoiceBot into a reasonable GDPR-ready state. It is not legal advice, but it gives the product and operations team a concrete implementation list.

## Customer-Facing Basics

- Publish a `Privacy Policy` on the marketing site.
- Publish `Terms of Service` on the marketing site.
- Add a privacy contact email for access, correction, deletion, and complaint requests.
- Get legal review of the privacy policy and terms before public launch, especially for New Zealand Privacy Act 2020 obligations.
- Explain key subprocessors in the privacy policy:
  - Railway / hosting
  - PostgreSQL database hosting
  - Stripe
  - Mailjet
  - OpenAI for voice transcription

## Lawful Basis And Documentation

- Document the lawful basis for each major processing activity.
- Use `contract` for core invoice generation and service delivery.
- Use `legitimate interests` for product security, fraud prevention, operational logging, and support handling where appropriate.
- Keep a simple record of processing activities:
  - what data is collected
  - where it comes from
  - why it is used
  - who receives it
  - how long it is retained

## Data Inventory

- Telegram account identifiers
- Business profile details
- Client names, emails, phone numbers, and addresses
- Invoice content and generated PDFs
- Support tickets and operational logs
- Billing metadata from Stripe
- Voice transcripts and any temporary audio handling notes

## Security Controls

- Admin dashboard protected by password + TOTP
- Strong access control on Railway, Stripe, Mailjet, and GitHub
- Encrypted secrets management
- Limit production access to the minimum number of people
- Define a breach-response process and internal owner

## User Rights Handling

- Create a manual process for:
  - export my data
  - delete my data
  - correct my data
  - object to non-essential processing
- Add admin tooling later for:
  - export one user
  - delete one user
  - audit user data by Telegram ID or customer record

## Retention

- Define how long to keep:
  - active invoice drafts
  - generated invoices
  - client records
  - support tickets
  - voice transcripts
  - payment event metadata
- Document when data is deleted or anonymized

## Vendor / Processor Actions

- Accept or sign DPAs / data-processing terms with each processor
- Review international transfer mechanisms for hosted vendors
- Keep a simple subprocessors list in the privacy policy or ops docs

## Marketing / Promotions

- Do not treat preference selection alone as sufficient legal sign-off for commercial promotions.
- Review the affiliate / promotion consent flow against the Unsolicited Electronic Messages Act 2007 before public launch.
- Make sure commercial messages have:
  - a lawful consent basis
  - sender identification
  - a working unsubscribe / opt-out path
  - internal records showing how consent was obtained

## Product Work Still Recommended

- Add user data export flow
- Add user deletion flow
- Add privacy request handling notes in the admin dashboard
- Add retention jobs for stale drafts and non-essential data
- Review whether analytics / cookies require separate consent before adding them

## Status

### Implemented now

- Public privacy page
- Public terms page
- Privacy contact route on the site
- Admin user data export tooling
- Admin user data deletion tooling
- Minimized invoice activity list exposure in the admin dashboard
- Retention policy document
- Daily cleanup job for stale drafts and other non-essential data
- Internal breach-response playbook

### Still to implement

- Formal subprocessors register page or section
- Full admin 2FA enrollment flow with recovery codes
- Role-based admin access if multiple operators need different permissions
- Legal review of privacy policy / terms for NZ launch
- Legal review of affiliate promotions consent and unsubscribe flow
