---
name: risk-acceptance
description: Prepare a residual-risk acceptance record for an authorized person to approve. Drafts only; never accepts, signs or fills in the approver. Use when a MEDIUM or higher risk cannot be mitigated in this change.
---

# Risk acceptance

An AI agent never accepts risk. This skill prepares the decision for a person.

1. Identify the RISK row in `security.md`: threats, likelihood, impact, level.
2. Explain plainly what can happen, to whom, how likely, the blast radius, and why it cannot be mitigated now.
3. Propose compensating controls and an expiry date (for example the next release or 90 days).
4. Show the row for `## Risk acceptance` in `gate.md`, leaving **Approved by**, **Role** and **Date** empty:
   `| RISK-NN | <decision and conditions> | | | | <expiry> |`
5. Only after the person fills in their name, role and date: set the RISK row to `Treatment: ACCEPT`,
   `Status: ACCEPTED`. Until then it stays OPEN.

Who may accept is the person accountable for the product or for security, as the team defines it. When
the acceptance expires, the risk is OPEN again.
