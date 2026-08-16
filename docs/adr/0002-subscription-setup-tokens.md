# Subscription setup tokens — never API keys, never an org-wide token

Status: accepted

Every automation on the box that runs Claude gets its own setup token, minted at
deploy time with `claude setup-token` from whatever subscription the automation's
*owner* is signed into on the deploying machine, written straight into that
automation's private `.credentials/` folder. There is no Anthropic API key anywhere
in the kit, and no single shared token for the box.

The alternatives were an API key (metered billing on a key someone has to create,
fund and hold) and one org-wide token covering every automation. Both were rejected
for the same reason: they detach usage from the person causing it. With per-owner
setup tokens, owners spend their own seat's usage, the manifest's `owner` field is
also the billing answer, and revoking one person removes one automation's access
rather than everyone's.

## Consequences

- Deploying a Claude automation requires the owner to be at the machine — minting
  opens their browser once. This is deliberate; it is what ties the token to a person.
- The token is captured and shipped in one shell call and never printed, echoed or
  narrated, consistent with the standing rule that credentials move programmatically
  and never through the model's context.
- Automations owned by different people hold different tokens on the same box; there
  is no shared credential to rotate centrally, and no org-level kill switch.
- If a subscription lapses or the token is revoked, only that owner's automations
  stop.
