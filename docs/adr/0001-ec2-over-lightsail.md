# EC2 over Lightsail

Status: accepted

The box is an EC2 instance, provisioned with `aws ec2 run-instances` against a
per-region Ubuntu 24.04 ARM AMI resolved from the SSM public parameter store, on
`t4g` (ARM) sizes with a `gp3` root volume. Lightsail was the obvious alternative
for this audience — flat monthly bundles and a much smaller surface to explain to a
non-technical owner.

EC2 wins because every server-lifecycle verb then rides one path the kit already has
to set up: the AWS CLI plus the `claude-assistant` IAM user at PowerUserAccess.
Provision, scale and remove are all `aws ec2` calls, ARM `t4g` gives the cheapest
sizes that comfortably run headless Claude Code and headless Playwright, and the
region is whatever the member's CLI is configured for rather than a second product's
region list.

## Consequences

- The skill scripts what Lightsail would have bundled: security group, key pair, AMI
  lookup, EBS sizing. That choreography lives in the PROVISION verb and has to stay
  correct.
- Cost is a stated estimate (~US$12–18/mo for t4g.small plus ~US$2 for the disk),
  not a flat bundle price, so the skill always states cost and gets a yes before
  launching.
- The box is ARM. Scaling must stay inside the `t4g` family (or another `g`-suffixed
  ARM family) — an x86 size will not boot.
- Stopping and starting the instance changes its public IP, so the instance id in the
  box record is the source of truth and the SSH config is refreshed after any
  stop/start.
