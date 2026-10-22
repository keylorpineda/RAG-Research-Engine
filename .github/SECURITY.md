# Security policy

## Reporting a vulnerability

Please **do not open a public issue**. Report it privately through
[GitHub security advisories](https://github.com/keylorpineda/RAG-Research-Engine/security/advisories/new).
You will get an answer within 7 days.

## Deployment model

The API has no authentication: it is meant to run on a private network or behind an authenticating
proxy. Do not expose it to the internet as is.

## What is in place

- Uploaded files are stored under server-generated names inside `UPLOADS_DIR`, with a size limit enforced while streaming.
- Error responses never include exception text, provider responses or file paths; details go to the server log.
- API keys are read from the environment and never logged.
- Dependencies are pinned in `uv.lock` and updated weekly by Dependabot.
