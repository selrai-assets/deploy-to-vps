# Issue tracker: Linear

Issues and specs for this repo live in Linear, worked via the Linear MCP tools (`mcp__linear__*`).

## Where issues go

- **Team**: Core Builds (key `CORE`, id `31b5d025-ec1d-4a51-983d-a811b52d7a34`)
- **Default project**: "deploy-to-vps: battle test and harden" (id `1f7803ae-e028-420c-9585-aadaaeb81b81`)

New issues for this repo go on the Core Builds team and, unless they clearly belong elsewhere, into that project.

## Conventions

- **Create an issue**: `mcp__linear__save_issue` with the team id, project id, a title, and a markdown description. Use real newlines, not `\n` escapes.
- **Read an issue**: `mcp__linear__get_issue` by identifier (e.g. `CORE-123`); fetch comments with `mcp__linear__list_comments`.
- **List issues**: `mcp__linear__list_issues` filtered by team/project/label/state.
- **Comment**: `mcp__linear__save_comment`.
- **Apply / remove labels**: set `labels` via `mcp__linear__save_issue`; create missing labels with `mcp__linear__create_issue_label` (check `mcp__linear__list_issue_labels` first).
- **Close / wontfix**: set the issue state via `mcp__linear__save_issue` (`Done` or `Canceled`; look up state ids with `mcp__linear__list_issue_statuses`).

## Pull requests as a triage surface

**PRs as a request surface: no.**

## When a skill says "publish to the issue tracker"

Create a Linear issue as above.

## When a skill says "fetch the relevant ticket"

`mcp__linear__get_issue` (plus `list_comments`) for the referenced identifier.
