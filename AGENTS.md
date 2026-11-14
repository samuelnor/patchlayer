## Commit conventions

Use [Conventional Commits](https://www.conventionalcommits.org/) with a [gitmoji](https://gitmoji.dev/) placed right after the colon:

```
<type>(<optional scope>)<optional !>: <gitmoji> <subject>
```

- Keep the type first so tooling that parses Conventional Commits keeps working.
- Write the gitmoji as the Unicode emoji (✨), not the `:shortcode:`.
- Subject: imperative mood, lowercase, no trailing period, at most ~72 characters.
- Breaking changes: add `!` after the type/scope and use 💥, plus a `BREAKING CHANGE:` footer.

| Type       | Gitmoji | Use for                               |
| ---------- | ------- | ------------------------------------- |
| `feat`     | ✨      | New feature                           |
| `fix`      | 🐛      | Bug fix                               |
| `docs`     | 📝      | Documentation only                    |
| `style`    | 🎨      | Formatting / code structure, no logic |
| `refactor` | ♻️      | Refactor without behaviour change     |
| `perf`     | ⚡️      | Performance improvement               |
| `test`     | ✅      | Add or update tests                   |
| `build`    | 📦️      | Build system or dependencies          |
| `ci`       | 👷      | CI configuration                      |
| `chore`    | 🔧      | Config, tooling, maintenance          |
| `revert`   | ⏪️      | Revert a previous commit              |

If a more specific gitmoji fits (e.g. 🔒️ security fix, 🚑️ hotfix, 🗃️ database changes), use it, but keep the matching type.

Examples:

```
feat(api): ✨ add patch preview endpoint
fix: 🐛 handle empty diff in parser
feat(config)!: 💥 rename settings file to patchwise.toml
```

## Agent skills

### Issue tracker

Issues live in GitHub Issues for samuelnor/patchwise, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Uses the five default label names: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Pull requests

Nothing lands on `main` without a PR and one peer approval. Work on a short-lived branch named after its lane (`nucleo/...`, `formal/...`, `corpus/...`, `entrega/...`) and open small PRs, one per piece that unblocks another lane.

When you open a PR, request the author's paired reviewer with `gh pr create --reviewer <login>`:

| Lane              | Author login    | Reviewer login  |
| ----------------- | --------------- | --------------- |
| Núcleo            | `DannyBaranshi` | `jdbu2002`      |
| Capa formal       | `jdbu2002`      | `DannyBaranshi` |
| Corpus            | `Diornon`       | `samuelnor`     |
| Evidencia humana  | `samuelnor`     | `Diornon`       |

- Find the author with `gh api user --jq .login`.
- If the reviewer has not answered in 10 minutes, any other team member may approve.
- Review checks two things only: the change respects the case and expediente format (issue #6), and the end-to-end case still runs. Style is not discussed.
- The author merges with squash after one approval.
