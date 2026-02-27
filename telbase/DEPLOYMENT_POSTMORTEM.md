# Telbase Deployment Post-Mortem

**Project**: NVIDIA DCF Valuation Model (SvelteKit + FastAPI + Neon PostgreSQL)
**Date**: February 27, 2026
**Outcome**: Deployed successfully after ~2 hours and ~9 deploy cycles
**Expected time**: 10-15 minutes

---

## Executive Summary

Deploying a standard two-service monorepo (SvelteKit frontend + FastAPI backend with PostgreSQL) to Telbase took ~2 hours instead of ~10 minutes. The root causes fall into three categories:

1. **Multi-service detection never activated** — we manually deployed each service as separate projects instead of using the monorepo orchestration that Telbase's CLI already supports
2. **The 3.5-minute GCP build feedback loop** made every issue cost 3.5+ minutes to test, turning 6 bugs into ~25 minutes of pure idle waiting
3. **No log streaming** — when the backend returned 500, we had no way to see why except adding a debug endpoint and redeploying (another 7 min round-trip)

The deployment exposed real, fixable gaps in Telbase's Python/asyncpg/Neon pipeline and in the multi-service detection for non-JS monorepos.

---

## The Actual Timeline

| Deploy # | What happened | Time lost | Root cause |
|----------|---------------|-----------|------------|
| 1 | Backend 500 — no DATABASE_URL | ~5 min | DB provisioned but URL not injected as env var |
| 2 | Backend 500 — `sslmode` crash | ~7 min | asyncpg rejects `sslmode=require` in Neon URL |
| 3 | Backend 500 — `gunicorn: command not found` | ~7 min | GCP Buildpacks don't expose gunicorn in PATH |
| 4 | Backend 500 — cached failed revision | ~10 min | GCP reused cached broken container, no rebuild |
| 5 | **Deleted all projects, started fresh** | ~5 min | Only way to escape cached failed revision |
| 6 | Backend 500 — wrong DATABASE_URL | ~7 min | New Neon instance created but old URL still set |
| 7 | Backend healthy, DB empty | ~7 min | Excel file not in git, so not deployed |
| 8 | Backend healthy, seed fails silently | ~7 min | Header detection bug + column size too small |
| 9 | Seeding works, everything live | — | Added debug endpoint, diagnosed, fixed |

**Total build wait time**: ~55 minutes (9 deploys x ~3.5 min average + cold start waits)
**Total debugging time**: ~50 minutes (diagnosing without logs, reading GCP console, adding debug endpoints)
**Total time**: ~2 hours

---

## The Six Issues in Detail

### Issue 1: asyncpg + Neon `sslmode` Incompatibility

**The #1 Python deployment footgun.**

Neon PostgreSQL connection strings include `sslmode=require`:
```
postgresql://user:pass@host/db?sslmode=require
```

asyncpg does NOT accept `sslmode` as a URL parameter. It crashes at connection time:
```
TypeError: connect() got an unexpected keyword argument 'sslmode'
```

SQLAlchemy 2.0.25's asyncpg dialect does NOT auto-translate this. The fix requires two coordinated changes:

**config.py** — Strip `sslmode` from the async URL, preserve it for sync:
```python
def _convert_for_asyncpg(url: str) -> str:
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    params.pop("sslmode", None)  # asyncpg can't handle this
    new_query = urlencode(params, doseq=True)
    return parsed._replace(query=new_query).geturl()
```

**database.py** — Pass SSL via `connect_args` instead:
```python
_connect_args = {}
if settings.database_ssl:
    _ssl_ctx = ssl_module.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl_module.CERT_NONE
    _connect_args["ssl"] = _ssl_ctx

engine = create_async_engine(
    settings.database_url,
    connect_args=_connect_args if "asyncpg" in settings.database_url else {},
)
```

**What Telbase should do**: When provisioning Neon for a Python app with asyncpg in `requirements.txt`:
- Either inject `DATABASE_URL` without `sslmode` and document the SSL context pattern
- Or inject two env vars: `DATABASE_URL` (without sslmode) and `DATABASE_SSL=true`
- At minimum: warn in the generated CLAUDE.md

This affects every FastAPI + asyncpg + Neon deployment. It's not an edge case.

---

### Issue 2: DATABASE_URL Not Auto-Injected

`telbase deploy --database` provisioned a Neon instance but did not set `DATABASE_URL` as an environment variable on the backend service. The stated reason was "no ORM detected" — but `requirements.txt` contained:
```
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
psycopg2-binary==2.9.9
alembic==1.13.1
```

**What Telbase should do**: If `--database` provisions a database, unconditionally inject `DATABASE_URL`. The user explicitly asked for a database. The detection of "which ORM" is a nice-to-have for format optimization, but the env var injection should not be gated on ORM detection. A provisioned database with no connection string is useless.

---

### Issue 3: GCP Build Cache Poisoning

This was the most destructive issue. The sequence:

1. Deploy succeeds (container image built)
2. Container crashes on startup (asyncpg sslmode error)
3. GCP marks the revision as failed
4. Next deploy: GCP reuses the cached container image **without rebuilding**
5. Same crash, same error, no build logs visible
6. Repeat steps 4-5 indefinitely

**The only escape**: Delete the entire Telbase project and recreate it.

This cost ~15 minutes (diagnosing why no build logs appeared + the nuclear delete + recreate + reconfigure env vars).

**What Telbase should do**:
- Detect when the previous revision failed to start → force a new build
- Or expose `--force-rebuild` flag
- At minimum: when a deploy shows no build logs, surface a message: "Reusing cached image from previous build. If the previous revision failed, try --force-rebuild"

---

### Issue 4: GCP Buildpacks Procfile Requirement

Without a `Procfile`, GCP Buildpacks couldn't determine how to start FastAPI. The default entrypoint used gunicorn, but:
- `gunicorn` was not importable from the Procfile's execution context (installed in a separate pip layer)
- Even if it were, gunicorn doesn't support ASGI natively

The fix was a one-line `Procfile`:
```
web: python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

**What Telbase should do**: The CLI already detects "FastAPI" as the framework. When deploying to GCP and no Procfile exists:
- Auto-generate one, or
- Warn: "No Procfile found. GCP Buildpacks require a Procfile for FastAPI. Generating: `web: python -m uvicorn main:app --host 0.0.0.0 --port $PORT`"

The detection intelligence is already there — `internal/detector/` has 18 files and 6.4K lines. This is a ~20-line addition.

---

### Issue 5: No Application Logs

When the backend returned HTTP 500, there was zero visibility into why. No `telbase logs nvidia-api`. No log streaming. No way to see the actual Python traceback.

To diagnose the sslmode crash and the seeding failure, we had to:
1. Add a `/admin/debug` endpoint to the FastAPI app
2. Redeploy (3.5 minutes)
3. curl the debug endpoint
4. Read the error
5. Fix the code
6. Remove the debug endpoint
7. Redeploy again

**Two deploy cycles (7 minutes) just to see an error message.**

This was the single biggest time multiplier. Every other issue (sslmode, seeding, column size) would have been diagnosed in seconds with log access.

**What Telbase should do**: `telbase logs <project-name>` that streams GCP Cloud Run logs (or Vercel function logs). The GCP Logging API and `gcloud run services logs read` both support this. Even a simple "show last 50 log lines after deploy" would help enormously.

---

### Issue 6: Excel Data File Not Deployed

`backend/data/NvidiaJan2025.xlsx` existed locally but wasn't tracked in git. Since Telbase deploys from git-tracked files (via tarball), the file was missing in production. The seeding code found empty tables but no Excel file to seed from, and logged a warning — which we couldn't see (Issue 5).

**What Telbase should do**: The tarball builder has access to both the git index and the working directory. When large files exist in the deploy directory but aren't git-tracked:
- Warn: "Found 1 untracked file in deploy directory (277KB total). These will NOT be deployed. Run `git add backend/data/NvidiaJan2025.xlsx` to include them."

---

## Multi-Service: What Should Have Happened

### The Repo Structure

```
nvidia-valuation-model/
  backend/           ← FastAPI (requirements.txt, app/)
  frontend/          ← SvelteKit (package.json, svelte.config.js)
  data/              ← Shared reference data
  docker-compose.yml ← Defines db service
  .env.example       ← Shows DATABASE_URL, VITE_API_URL patterns
```

### What the CLI's DetectMonorepo() Actually Did (Code-Level Analysis)

We traced the exact execution path through the Telbase CLI source code (`internal/detector/monorepo.go`, `cmd/deploy.go`). The multi-service detection code was compiled and present — the binary was built the same day (Feb 27 12:26). **The issue was not missing code or a stale binary.**

The root cause is a **self-check gate** at the top of `DetectMonorepo()`:

```go
// monorepo.go lines 32-38
func DetectMonorepo(dir string) (*MonorepoResult, error) {
    // If this directory IS a deployable project, it's not a monorepo root
    if isDeployableProject(dir) {
        return nil, nil  // ← exits immediately, no multi-service
    }
    // ... workspace detection, subdirectory scanning never reached ...
}
```

We deployed from `nvidia-valuation-model/backend/`, which is a valid FastAPI project (has `requirements.txt` with `fastapi`). So `isDeployableProject("/path/to/backend")` returned `true`, and `DetectMonorepo()` returned `nil` — **multi-service detection was never attempted**.

This is correct behavior in isolation: if you're standing in a deployable directory, treat it as a single project. But it creates a UX trap: deploying from a subdirectory of a monorepo silently skips multi-service orchestration with no warning.

#### The call chain in deploy.go:

```
cmd/deploy.go:579  →  DetectMonorepo(cwd)
                       ↓
                   cwd = /path/to/backend
                       ↓
                   isDeployableProject(cwd) = true (FastAPI)
                       ↓
                   return nil, nil   ← multi-service SKIPPED
                       ↓
cmd/deploy.go:585  →  proceed with single-service deploy
```

#### What would have happened from the repo root:

```
cmd/deploy.go:579  →  DetectMonorepo(cwd)
                       ↓
                   cwd = /path/to/nvidia-valuation-model
                       ↓
                   isDeployableProject(cwd) = false (no requirements.txt/package.json at root)
                       ↓
                   scanSubdirectories(cwd)
                       ↓
                   Found: backend/ (FastAPI) + frontend/ (SvelteKit) = 2 candidates
                       ↓
                   return MonorepoResult{Services: [backend, frontend]}
                       ↓
cmd/deploy.go:590  →  runMultiServiceDeploy()  ← WOULD HAVE WORKED
```

**Multi-service would have activated correctly if we had deployed from the repo root.** The subdirectory scanning logic (`scanSubdirectories`) would have found both `backend/` and `frontend/` as independent deployable projects and triggered `runMultiServiceDeploy()` with priority ordering (backend+DB first, then frontend).

#### The UX gap:

The CLI has `FindProjectConfig()` (in `internal/config/project.go`) which walks UP from the current directory to find an existing `.telbase/config.json`. This helps for *subsequent* deploys from subdirectories after multi-service has already been configured. But on the **first deploy**, there's no config to find, so the upward walk finds nothing. There's no "you're inside a monorepo" warning when deploying from a subdirectory for the first time.

### What Should Have Happened

Running `telbase deploy` from the repo root would have:

1. **Detected two services**:
   - `backend/` → FastAPI (requirements.txt with fastapi) → GCP Cloud Run
   - `frontend/` → SvelteKit (package.json with @sveltejs/kit) → Vercel

2. **Read `.env.example`** to understand the env var contract:
   - Backend needs `DATABASE_URL`
   - Frontend needs `VITE_API_URL` pointing to backend

3. **Read `docker-compose.yml`** to understand the database dependency:
   - PostgreSQL required → provision Neon

4. **Deployed in priority order** (backend+DB first, then frontend):
   - Provision Neon database
   - Set `DATABASE_URL` on backend (asyncpg-compatible, without sslmode)
   - Deploy backend → get URL `https://nvidia-api.telbase.ai`
   - Set `VITE_API_URL=https://nvidia-api.telbase.ai` on frontend
   - Set `CORS_ORIGINS=["https://nvidia-frontend.telbase.ai"]` on backend
   - Deploy frontend

5. **Total time**: ~5 minutes (one GCP build + one Vercel build in parallel after DB provisioning)

### Detection Signals That Were Available

| Signal | Location | What it tells you |
|--------|----------|-------------------|
| `docker-compose.yml` with `postgres:15-alpine` | Repo root | Database dependency |
| `backend/requirements.txt` with `fastapi`, `asyncpg` | Backend dir | Stack + driver |
| `frontend/package.json` with `@sveltejs/kit` | Frontend dir | Stack |
| `.env.example` with `VITE_API_URL` | Repo root | Frontend → backend connection |
| `.env.example` with `DATABASE_URL` using `asyncpg` | Repo root | DB URL format preference |
| No root `package.json` | Repo root | NOT a JS workspace monorepo |
| Two directories with independent dependency files | Repo structure | Subdirectory monorepo pattern |

The `docker-compose.yml` signal is particularly strong. If a repo has docker-compose with service definitions matching subdirectory names, that's a high-confidence monorepo signal even without a workspace manifest.

---

## Concrete Recommendations

### Tier 1: Would Have Prevented This Entirely

**1. `telbase logs <project>`**
Stream application logs from GCP Cloud Run / Vercel. This alone eliminates 2-3 deploy cycles per debugging session. Implementation: wrap `gcloud run services logs read` for GCP, Vercel Logs API for Vercel.

**2. asyncpg-aware DATABASE_URL injection**
When deploying Python + asyncpg + Neon:
- Strip `sslmode=require` from injected `DATABASE_URL`
- Set `DATABASE_SSL=true` as a separate env var
- Document the `connect_args` SSL pattern in generated CLAUDE.md

Add to `internal/detector/`: `asyncpg.go` (~50 lines) that reads `requirements.txt` for asyncpg and transforms the Neon URL accordingly.

**3. Force rebuild on failed revision**
When the previous GCP Cloud Run revision status is "failed", force a fresh build instead of reusing the cached image. The Cloud Run API exposes revision status — check it before triggering the build.

### Tier 2: Would Have Saved Significant Time

**4. Auto-generate Procfile for FastAPI on GCP**
Detection already identifies FastAPI. When no Procfile exists and target is GCP:
```
web: python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```
Add to `internal/detector/procfile.go` or as a pre-deploy hook in `deploy-gcp.ts`.

**5. Unconditional DATABASE_URL injection with `--database`**
If the user explicitly passes `--database`, always inject `DATABASE_URL`. Don't gate on ORM detection. The user asked for a database — give them the connection string.

**6. Upward-looking monorepo warning on subdirectory deploy**
The `DetectMonorepo()` self-check gate is correct in isolation, but it silently swallows a critical UX case. When deploying from a subdirectory for the first time, the CLI should look UP to the git root and check for other deployable siblings. A ~10-line fix:

```go
// In DetectMonorepo(), after the self-check gate returns nil:
if isDeployableProject(dir) {
    // Before returning, check if we're inside a larger monorepo
    gitRoot := findGitRoot(dir)
    if gitRoot != "" && gitRoot != dir {
        result, _ := scanSubdirectories(gitRoot)
        if result != nil && len(result.Services) >= 2 {
            log.Warnf("Deploying single service from %s, but %d services "+
                "detected in repo root %s. Run `telbase deploy` from %s "+
                "for multi-service orchestration.", dir, len(result.Services),
                gitRoot, gitRoot)
        }
    }
    return nil, nil
}
```

Additionally, `scanSubdirectories()` should recognize non-JS monorepo signals:
- Two+ directories with independent dependency files (`requirements.txt`, `package.json`, `go.mod`)
- `docker-compose.yml` with service definitions matching directory names
- `.env.example` with cross-service env vars (`VITE_API_URL`, `CORS_ORIGINS`)

### Tier 3: Polish

**7. Untracked file warnings**
When building the deploy tarball, warn about untracked files >10KB in the deploy directory.

**8. Richer generated CLAUDE.md**
Include known issues for the detected stack:
```markdown
### Known Issues — FastAPI + asyncpg + Neon
- asyncpg rejects `sslmode=require` in URLs. Strip it and use connect_args SSL.
- GCP Buildpacks require a Procfile. Use `python -m uvicorn`, not `gunicorn`.
- Only git-tracked files are deployed.
- Add `.python-version` to pin Python version on GCP.
```

**9. `telbase dev` for local simulation**
Run the Worker reverse proxy locally with injected production env vars. Would catch CORS, path prefix, and env var issues before deploying.

---

## Architecture Notes for Future Deployments

### What We Changed to Make It Work

| File | Change | Why |
|------|--------|-----|
| `backend/app/config.py` | Added `_convert_for_asyncpg()` to strip sslmode, derive sync URL | asyncpg URL incompatibility |
| `backend/app/database.py` | Added SSL context via `connect_args`, wrapped in try/except | asyncpg SSL + resilient startup |
| `backend/app/main.py` | Background `asyncio.create_task(_init_database())` | GCP cold start: app must respond to health checks before DB is ready |
| `backend/Procfile` | `web: python -m uvicorn main:app --host 0.0.0.0 --port $PORT` | GCP Buildpacks need explicit entrypoint |
| `backend/.python-version` | `3.12.9` | Pin Python version for GCP |
| `backend/main.py` | Thin entry point: `from app.main import app` | uvicorn needs importable module at workspace root |
| `backend/app/models/country.py` | `moodys_rating` from `String(10)` to `String(30)` | Excel data had longer rating strings |
| `backend/app/seed/seed_from_excel.py` | Header detection: match exact column header, not sheet title | Sheet title "Country equity risk premiums" was false-matching |
| `frontend/src/lib/services/api.ts` | Remove `/api` suffix from `API_BASE` | Worker reverse proxy strips `/api` prefix before forwarding |

### Environment Variables Set Manually

| Service | Variable | Value | Should be auto-injected? |
|---------|----------|-------|--------------------------|
| Backend | `DATABASE_URL` | `postgresql://...@neon.tech/neondb?sslmode=require` | Yes — `--database` should do this |
| Backend | `CORS_ORIGINS` | `["https://nvidia-frontend.telbase.ai"]` | Yes — multi-service should do this |
| Frontend | `VITE_API_URL` | `https://nvidia-api.telbase.ai` | Yes — multi-service should do this |

All three env vars should have been auto-injected by a working multi-service deploy pipeline.

### GCP Cloud Run Specifics Learned

- **Buildpacks CWD**: `/workspace/` (contents of the deployed directory)
- **Python**: Uses `.python-version` to select runtime. Defaults to latest 3.x without it.
- **Pip layer**: Installed to `/layers/google.python.pip/pip`, not system PATH. Custom Procfile commands can't call `gunicorn` directly.
- **Health checks**: GCP pings `/` or the configured health check endpoint before routing traffic. The app must respond before the timeout (~300s default).
- **Revision caching**: If revision N fails to start and you deploy N+1 with no source changes, GCP may reuse revision N's image.
- **Build time**: ~3.5 min for a medium Python app (fastapi + numpy + scipy + pandas + openpyxl).

---

## Final Deployment State

| Component | URL | Status |
|-----------|-----|--------|
| Backend API | https://nvidia-api.telbase.ai | Live |
| API Docs | https://nvidia-api.telbase.ai/docs | Live |
| Frontend | https://nvidia-frontend.telbase.ai | Live |
| Database | Neon PostgreSQL (us-west-2) | Connected |

| Reference Data | Count |
|---------------|-------|
| Countries | 203 |
| US Industries | 94 |
| Global Industries | 95 |
| Synthetic Ratings | 30 |

---

## The Bottom Line

Telbase's multi-service architecture — workspace detection, priority-ordered deploys, env var scoping, change detection, Worker path routing — is genuinely sophisticated infrastructure. **It would have worked.** Running `telbase deploy` from the repo root would have detected both services, orchestrated the deploys in the right order, and wired up the env vars automatically. The subdirectory scanning code correctly identifies `backend/` (FastAPI) and `frontend/` (SvelteKit) as independent deployable projects.

But we deployed from `backend/`, and `DetectMonorepo()` has a self-check gate: if the current directory IS a deployable project, return nil immediately. This is architecturally sound — a directory that is itself deployable shouldn't be treated as a monorepo root. But with no upward-looking warning, the user has no way to know they're standing in one room of a house that the CLI could have furnished automatically.

The gap is not in **capability** but in **discoverability**. The detection intelligence exists (`internal/detector/` has 18 files, 6.4K lines). The multi-service orchestration exists (`runMultiServiceDeploy()` with priority ordering). The env var scoping exists. All of it was compiled into the binary we used. We just invoked it from the wrong directory, and nothing told us.

Three changes would have collapsed this 2-hour session into 10 minutes:
1. **Log streaming** — see errors instantly instead of deploying debug endpoints
2. **asyncpg-aware URL injection** — eliminate the #1 Python+Neon footgun
3. **Upward-looking monorepo warning** — when deploying from a subdirectory, check the git root for sibling services and warn the user

These aren't feature requests. They're the difference between "it just works" and "I spent 2 hours debugging a standard two-service app."
