# Deploying the demo

The web app is static and goes on Vercel. The API and its database have three routes:

| | A. Render + Neon | B. One Oracle Cloud VM | C. Heroku |
| :-- | :-- | :-- | :-- |
| Cost | Free | Free (Always Free) | About 12 USD a month: Basic dyno + Postgres Essential-0, covered by the GitHub Student Pack credit (13 USD a month, 24 months) |
| API | 512 MB, sleeps after 15 min idle, ~1 min to wake | Ampere A1 VM, up to 4 cores and 24 GB | 512 MB, always on |
| Database | Neon Postgres with pgvector | Postgres + pgvector in Docker on the VM | Heroku Postgres with pgvector |
| Embeddings | Cohere (local models do not fit in 512 MB) | Local or Cohere | Cohere |
| You maintain | Nothing | The VM: updates, firewall | Nothing |

All three use the same image (`Dockerfile`). Its entrypoint applies the migrations, then serves on
`$PORT`. Keys live only in the host's settings, never in the repository or the web app.

## Demo settings

| Variable | Demo value | Why |
| :-- | :-- | :-- |
| `UPLOADS_ENABLED` | `false` | Visitors ask about the preloaded PEPs; nothing is written to disk. |
| `DAILY_QUESTION_LIMIT` | `15` | Counted in the `queries` table. A Cohere trial key allows about 1,000 calls a month, and a question costs two (embed + rerank). |
| `QUESTIONS_PER_CLIENT_PER_HOUR` | `5` | So one visitor cannot spend the day's questions. |
| `ANSWER_CACHE_SIZE` | `256` | Repeated questions, such as the suggested ones, are answered from memory: free, and not counted. |
| `LEXICAL_TRANSLATION` | `true` | Spanish questions also match the English PEPs in full-text search (docs/BENCHMARKS.md). |
| `TRUST_PROXY_HEADERS` | `true` | Read the visitor's address from `X-Forwarded-For`, set by Vercel and Render or Caddy. |
| `COHERE_*_PER_MINUTE` | `90000` / `90` / `9` | Stay under the trial key's per-minute limits. |

Use a Cohere key for the demo only, separate from development: one benchmark run spends about 350
calls. When the daily cap or the monthly quota runs out, the API answers `429` and the web app
says so in the visitor's language.

## A. Render + Neon

1. **Database.** Create a Neon project, then run `CREATE EXTENSION vector;` in its SQL editor. Copy
   the connection string and use the `postgresql+psycopg://…?sslmode=require` form.
2. **Load the PEPs** from your machine, with the same embedding settings the API will use:

   ```bash
   DATABASE_URL="postgresql+psycopg://…neon.tech/neondb?sslmode=require" \
   EMBEDDING_PROVIDER=cohere COHERE_API_KEY=… uv run python -m eval.seed
   ```

   This applies the migrations and ingests 26 PEPs (1,240 passages, about 15 Cohere calls). Run it
   again to resume an interrupted load; PEPs already present are skipped.
3. **API.** In Render, choose New → Blueprint and select this repository. `render.yaml` creates
   `research-engine-api` and asks for `DATABASE_URL`, `GROQ_API_KEY` and `COHERE_API_KEY`. Check
   `https://research-engine-api.onrender.com/api/health`.

## B. Oracle Cloud VM

1. Create an Always Free instance: Ubuntu, shape `VM.Standard.A1.Flex` (2 cores and 12 GB are
   plenty). Popular regions often report no capacity; retry later or try another region. In the
   subnet's security list, open TCP 80 and 443, and on the VM open them in the firewall too:

   ```bash
   sudo iptables -I INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT && sudo netfilter-persistent save
   ```

2. Install Docker, clone the repository, then:

   ```bash
   cd deploy/oracle && cp .env.example .env    # API_DOMAIN, POSTGRES_PASSWORD, GROQ_API_KEY…
   docker compose up -d --build
   docker compose exec api python -m eval.seed
   ```

   Without a domain of your own, `API_DOMAIN=api.<public-ip>.sslip.io` resolves to the VM, and
   Caddy obtains its HTTPS certificate. With `EMBEDDING_PROVIDER=local` there is no key and no
   quota, so `DAILY_QUESTION_LIMIT` can stay unset.
3. Update the VM now and then (`sudo apt upgrade`). Oracle can reclaim Always Free instances that
   stay almost idle for a week.

## C. Heroku

1. **App.** With the Heroku CLI, from the repository:

   ```bash
   heroku create research-engine-api --stack container
   heroku addons:create heroku-postgresql:essential-0
   heroku pg:psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

   Or use the Deploy button flow with `app.json`, which declares the same: container stack,
   a Basic dyno, the Postgres add-on and the demo settings.
2. **Settings.** `app.json` sets the demo values; add the keys:

   ```bash
   heroku config:set GROQ_API_KEY=… COHERE_API_KEY=… EMBEDDING_PROVIDER=cohere RERANK_PROVIDER=cohere      UPLOADS_ENABLED=false DAILY_QUESTION_LIMIT=15 QUESTIONS_PER_CLIENT_PER_HOUR=5      ANSWER_CACHE_SIZE=256 TRUST_PROXY_HEADERS=true
   ```

   Heroku sets `DATABASE_URL` (`postgres://…`); the API converts it to the psycopg driver.
3. **Deploy.** `git push heroku main`. `heroku.yml` builds the image without the local model
   (`EXTRAS=none`). Connecting the GitHub repository in the dashboard deploys `main` on every
   release instead.
4. **Load the PEPs** once, from your machine, with the database URL from
   `heroku config:get DATABASE_URL`:

   ```bash
   DATABASE_URL="$(heroku config:get DATABASE_URL)" EMBEDDING_PROVIDER=cohere COHERE_API_KEY=…      uv run python -m eval.seed
   ```

   Then point the Vercel rewrite at `https://<app>.herokuapp.com`.

## Web app on Vercel

1. Import the repository in Vercel with **Root Directory** `web`. `web/vercel.json` sets the pnpm
   install and build commands, the output folder, security headers, and the fallback that serves
   the app for every route.
2. Point the `/api/:path*` rewrite in `web/vercel.json` at your API (the Render URL, or
   `https://<API_DOMAIN>`). The browser then only talks to the Vercel origin, so no CORS is needed.
   To call the API from another origin instead, set `CORS_ORIGINS` on the API.
3. Every pull request gets a preview deployment.

## Check

- `GET /api/health` returns `"uploadsEnabled": false` and `questionsLeftToday`.
- On a phone, ask "What does PEP 8 recommend about line length?": the answer cites passages from
  `pep-0008.txt`.
- Ask "What is the capital of Australia?": the engine refuses and shows the evidence gauge.
