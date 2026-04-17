# ARC Configuration (Mock)

> Source: Test harness — not a real ARC config

## Coding Standards

- Python 3.11+, Django 4.2+, Django REST Framework
- Follow existing eda-server patterns (see `src/aap_eda/` for conventions)
- Use type hints on public functions
- Use `logging` module (not print statements)
- Imports: stdlib → django → third-party → local (isort enforced)

## Test Guidance

- Framework: pytest with pytest-django
- Fixtures: define in `conftest.py` at appropriate level
- Decorator: `@pytest.mark.django_db` for database tests
- API tests: use `admin_client` fixture with `force_authenticate`
- Naming: `test_<action>_<subject>_<scenario>`
- Location: `tests/integration/api/` for API tests, `tests/unit/` for unit tests

## Git Workflow

- Branch naming: `<type>/<ticket-id>-<description>`
- Commit format: `type(scope): message` with `Refs: AAP-XXXXX`
- PR required for merge to main

## Mock Overrides

For this SDLC test:
- **Jira source**: `.sdlc-test/jira/` (markdown files, not live Jira)
- **Handbook source**: `.sdlc-test/handbook/` (local markdown, not handbook repo)
- **Approvals**: Auto-approved (skip approval gates)
- **Session recording**: Disabled
