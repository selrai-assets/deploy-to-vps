# Issue tracker: Linear

Issues and specs for this repo live in Linear (the `selr-ai` workspace), not GitHub Issues — despite the GitHub remote. Use the Linear MCP tools (`mcp__linear__*`) for all operations.

## Where issues go

- **Team**: Client Delivery (key `CD`)
- **Project**: Ark Bathrooms ASA

This repo is the Selr-owned `deploy-to-vps` skill, tracked under the Ark Bathrooms ASA engagement because Ark/OA is its first drop target. If tracking later moves to a product-side project, edit these two lines — the skills read this file, not their own assumptions.

## Conventions

- **Create an issue**: `mcp__linear__save_issue` with `team: "Client Delivery"`, `project: "Ark Bathrooms ASA"`, plus title, markdown description, and labels.
- **Read an issue**: `mcp__linear__get_issue` (by `CD-<n>` identifier or id); `mcp__linear__list_comments` for the thread.
- **List issues**: `mcp__linear__list_issues` filtered by team/project/label/state.
- **Comment**: `mcp__linear__save_comment`.
- **Apply / remove labels**: `mcp__linear__save_issue` with the full desired `labels` array (it replaces, not merges — read the issue's current labels first).
- **Close**: `mcp__linear__save_issue` setting the state to Done (or Canceled for wontfix outcomes).

## Pull requests as a triage surface

**PRs as a request surface: no.** _(GitHub PRs on this repo are implementation traffic only; `/triage` ignores them.)_

## When a skill says "publish to the issue tracker"

Create a Linear issue in Client Delivery / Ark Bathrooms ASA.

## When a skill says "fetch the relevant ticket"

`mcp__linear__get_issue` with the `CD-<n>` identifier.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets. The Client Delivery team already carries the `wayfinder:*` labels.

- **Map**: a single issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body.
- **Child ticket**: a Linear sub-issue of the map (`parentId` on `save_issue`), labelled `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, assign the ticket to the driving dev.
- **Blocking**: Linear's native issue relations — mark the child as *blocked by* its blocker. A ticket is unblocked when every blocker is closed.
- **Frontier query**: list the map's open sub-issues, drop any with an open blocker or an assignee; first in map order wins.
- **Claim**: assign the issue to yourself — the session's first write.
- **Resolve**: comment the answer, move the issue to Done, then append a context pointer to the map's Decisions-so-far.
