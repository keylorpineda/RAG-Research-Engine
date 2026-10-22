# Contributing

Thanks for taking the time to improve the RAG Research Engine.

## Branches and releases

| Branch | Receives | Rules |
| :-- | :-- | :-- |
| `develop` (default) | Every change, through a pull request | PR required, `ci` and `pr-title` green, no force push |
| `main` | Release pull requests from `develop` only | PR required, `ci` green and up to date, no force push |

Each merge into `main` is a stable release, tagged `vX.Y.Z` ([Semantic Versioning](https://semver.org/)) and described in `CHANGELOG.md`. Nobody pushes to either branch directly, maintainers included.

## Workflow

1. Open or pick an issue. Every change starts from an issue with context, scope and acceptance criteria.
2. Branch from `develop` as `<type>/<issue>-<short-description>`, for example `fix/4-recency-scoring`.
3. Keep commits small and use [Conventional Commits](https://www.conventionalcommits.org/): `<type>(<scope>): <summary>`.
4. Open the pull request against `develop`. The PR title is a Conventional Commit too; it becomes the squash commit.
5. Feature PRs are squash-merged; release PRs (`develop` -> `main`) use a merge commit so both branches share history.

Scopes: `api`, `retrieval`, `ingestion`, `db`, `eval`, `web`, `deploy`, `ci`, `repo`, `deps`.

## Local checks

```bash
uv sync
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

## Retrieval changes need numbers

A change to chunking, embeddings, ranking or the abstention gate must include the benchmark table before and after it. A change that makes the numbers worse needs a reason in the PR description.

## Never commit

- `.env` or any API key.
- Uploaded documents or the benchmark corpus (`eval/corpus/` is downloaded, not versioned).
