# Research Engine · web

Angular 22 front end for the Research Engine API: standalone components, signals, zoneless change
detection, Vitest. Package manager: pnpm.

```bash
pnpm install
pnpm start          # http://localhost:4200, /api proxied to http://localhost:8000
pnpm test --watch=false
pnpm lint
pnpm build          # dist/web/browser
```

Start the API first (`docker compose up` from the repository root, or `uv run uvicorn app.main:app`).

## Layout

| Path | Contents |
| --- | --- |
| `src/styles/tokens.css` | Deep Ink design tokens, dark and light |
| `src/app/core/api` | Typed client for `/api/*`; failures become `ApiError` |
| `src/app/core/i18n` | English and Spanish copy, number formatting |
| `src/app/core/theme.service.ts` | Theme signal, saved in `localStorage` |
| `src/app/layout` | Header, footer, logo |
| `src/app/pages` | Lazy routes: ask, library, benchmarks |

In production the host rewrites `/api` to the backend, so the app always calls its own origin.
