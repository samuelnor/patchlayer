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
feat(config)!: 💥 rename settings file to patchlayer.toml
```

## Agent skills

### Issue tracker

Issues live in GitHub Issues for samuelnor/patchlayer, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Uses the five default label names: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
