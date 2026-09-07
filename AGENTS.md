# 注意事项

1. 每次改动完成后，都必须创建一个对应的 git commit 并推送到远端，以便后续追踪和回滚
2. 每次改动后，都必须编写或更新相关测试，并在交付给用户前，确保所有测试和验证都通过

## Agent skills

### Issue tracker

Issues are tracked as local markdown files in `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles use the default label strings. See `docs/agents/triage-labels.md`.

### Domain docs

Domain docs use the single-context layout: root `CONTEXT.md` plus `docs/adr/`. See `docs/agents/domain.md`.
