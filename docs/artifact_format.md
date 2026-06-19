# Markdown artifact format (15menit)

Templates adapted from **[hesoyam](https://github.com/anggiedimasta/hesoyam)**.

---

## Artifacts

| File | Role |
|------|------|
| [`prd.md`](./prd.md) | Product requirements, tech stack, data sources |
| [`backlog.md`](./backlog.md) | Phased backlog — Flow · Data · Behavior · Tests · Status |
| [`changelog.md`](./changelog.md) | Releases; auto-sync via `scripts/release-sync.mjs` |
| [`artifact_format.md`](./artifact_format.md) | This file |

---

## `docs/changelog.md`

- Preserve **`<!-- changelog:sync-begin -->`** … **`<!-- changelog:sync-end -->`** inside `## [Unreleased]`.
- Versions: **`## [x.y.z] - YYYY-MM-DD`**, newest first after `[Unreleased]`.
- **Do not** hand-edit content between sync markers; add manual notes outside them.

---

## `docs/backlog.md`

- Phased items (`P0-01`, …) with **Status** per item (Done / Partial / Blocked).
- Move status in item body during execution; no separate board table.
- Shipped work → reflected in changelog via git / release-sync.

---

## Version automation

- **`package.json` `version`** — SemVer; bumped by **`bun run release:cut`** / pre-push hook.
- **Pre-commit:** `.husky/pre-commit` → `bun run lint:staged` (Biome on staged files).
- **Pre-push:** `.husky/pre-push` → `scripts/release-sync.mjs --if-needed` (writes changelog + patch bump; may require second `git push`).

---

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/) with optional scope:

```
feat(web): commute compare panel
fix(api): geocode proxy rate limit
docs: GTFS source table
chore(release): v0.1.1 changelog sync   # automated — hook skips re-entry
```

Scopes: `web`, `api`, `docs`, `data`, `infra`.
