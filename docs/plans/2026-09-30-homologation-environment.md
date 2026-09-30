# Homologation Environment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Provision an isolated, zero-cost Supabase homologation database and connect dedicated Cloud Run and Netlify deployments to the `homologacao` branch.

**Architecture:** Keep `main` mapped to the existing production stack and map `homologacao` to separate Supabase, Cloud Run, and Netlify resources. Store no credentials in Git; use local environment files for manual operations and GitHub environment secrets for automated deployments. Apply the same Alembic migration chain to each database, homologation first.

**Tech Stack:** Supabase PostgreSQL, Alembic, FastAPI, GCP Cloud Run, Artifact Registry, Netlify, GitHub Actions, Make.

---

### Task 1: Establish a clean baseline

**Files:**
- No files changed

**Step 1: Verify branch isolation**

Run: `git status --short --branch`
Expected: branch `homologacao`, with only the implementation-plan document uncommitted.

**Step 2: Install existing project dependencies if absent**

Run: `cd frontend && npm install`
Expected: dependencies install without changing application source.

Run: `cd console && npm install`
Expected: dependencies install without changing application source.

**Step 3: Run baseline checks**

Run: `backend/.venv/bin/pytest backend/tests -q` when the shared environment is available, otherwise create/install the backend environment using the repository instructions.
Expected: all backend tests pass.

Run: `cd frontend && npm test -- --run`
Expected: all frontend tests pass.

Run: `cd console && npm test`
Expected: all console tests pass.

**Step 4: Commit this implementation plan**

```bash
git add docs/plans/2026-09-30-homologation-environment.md
git commit -m "docs: plan homologation environment"
```

### Task 2: Authenticate and provision Supabase Free

**Files:**
- Create locally, ignored: `backend/.env.homologation`
- Modify if needed: `.gitignore`

**Step 1: Install the Supabase CLI**

Run: `brew install supabase/tap/supabase`
Expected: `supabase --version` prints the installed version.

**Step 2: Authenticate interactively**

Run: `supabase login`
Expected: browser authentication succeeds without exposing the access token in chat or Git.

**Step 3: Inspect organizations and projects**

Run: `supabase orgs list` and `supabase projects list`
Expected: identify the production project and whether a separate Free organization/project slot is available.

**Step 4: Create only a zero-cost resource**

Create an organization/project named for Parrot Trips homologation using the Free plan. Stop before confirmation if the UI or API reports any charge.

Expected: a distinct Supabase project reference and database host, with plan Free / USD 0.

**Step 5: Save local runtime variables safely**

Write `backend/.env.homologation` with `DATABASE_URL`, a new `JWT_SECRET`, `APP_ENV=homologation`, and only test-safe integration credentials. Ensure the file is ignored.

**Step 6: Apply and verify migrations**

Run: `cd backend && set -a && source .env.homologation && set +a && env/bin/alembic upgrade head`
Expected: Alembic reaches the repository head revision.

Run: `cd backend && set -a && source .env.homologation && set +a && env/bin/alembic current`
Expected: current revision equals head.

### Task 3: Add explicit environment-aware deploy commands

**Files:**
- Modify: `Makefile`
- Modify: `.gitignore`
- Create: `backend/.env.homologation.example`
- Create: `frontend/.env.homologation.example`

**Step 1: Add a static configuration check**

Create a small shell-based Make target, `check-homolog-config`, that fails unless homologation uses a service name, Netlify site ID, and environment files distinct from production.

**Step 2: Run the check and confirm failure**

Run: `make check-homolog-config`
Expected: FAIL until homologation variables and targets exist.

**Step 3: Add homologation targets**

Add environment-specific variables and targets:

- `deploy-homolog`
- `deploy-backend-homolog`
- `deploy-frontend-homolog`
- `migrate-homolog`
- `homolog-backend-url`
- `logs-homolog`

Use `parrot-trips-backend-homolog`, `backend/.env.homologation`, `frontend/.env.homologation`, a distinct Netlify site ID, and commit-SHA image tags. Preserve all existing production targets unchanged.

**Step 4: Re-run the configuration check**

Run: `make check-homolog-config`
Expected: PASS.

**Step 5: Verify builds without deployment**

Run: `docker build --platform linux/amd64 -t parrot-trips-backend:homolog-test backend/`
Expected: backend image builds.

Run: `cd frontend && npm run build -- --mode homologation`
Expected: frontend builds using the homologation API URL.

**Step 6: Commit**

```bash
git add Makefile .gitignore backend/.env.homologation.example frontend/.env.homologation.example
git commit -m "feat: add isolated homologation deploy targets"
```

### Task 4: Provision Cloud Run homologation backend

**Files:**
- No tracked file changes expected

**Step 1: Verify GCP authentication and project**

Run: `gcloud auth list` and `gcloud config get-value project`
Expected: authorized account and project `jogo-da-vida-497700`.

**Step 2: Deploy the isolated backend**

Run: `make deploy-backend-homolog`
Expected: service `parrot-trips-backend-homolog` deploys without modifying `parrot-trips-backend`.

**Step 3: Validate health and environment**

Run: `curl -fsS "$(make -s homolog-backend-url)/healthz"`
Expected: HTTP success.

Confirm through a safe database query that the service sees only homologation test data.

### Task 5: Provision Netlify homologation frontend

**Files:**
- Create locally, ignored: `frontend/.env.homologation`
- Modify: `Makefile` with the actual homologation site ID

**Step 1: Verify Netlify authentication**

Run: `netlify status`
Expected: authenticated account is shown.

**Step 2: Create a separate site**

Run: `netlify sites:create --name parrot-trips-homolog`
Expected: a new site and opaque site ID, distinct from production.

**Step 3: Configure the frontend URL**

Set `VITE_API_URL` in `frontend/.env.homologation` to the homologation Cloud Run URL.

**Step 4: Deploy and smoke test**

Run: `make deploy-frontend-homolog`
Expected: production Netlify site remains untouched and the homologation URL loads successfully.

Test login only with test users and confirm requests target `parrot-trips-backend-homolog`.

**Step 5: Commit the non-secret site configuration**

```bash
git add Makefile
git commit -m "chore: configure homologation hosting"
```

### Task 6: Add branch-based CI/CD safely

**Files:**
- Create: `.github/workflows/deploy-homologation.yml`
- Create or modify: `.github/workflows/deploy-production.yml`
- Modify: `README.md`

**Step 1: Add workflow validation before deployment jobs**

Configure build/test jobs for backend and frontend. Deployment jobs require the corresponding GitHub Environment and only run for their mapped branch.

**Step 2: Configure homologation mapping**

`homologacao` may deploy only to the `homologation` GitHub Environment and homologation resource identifiers.

**Step 3: Configure production mapping**

`main` may deploy only to the `production` GitHub Environment and existing production resources. Preserve a manual approval gate for production if GitHub plan/settings support it.

**Step 4: Validate workflow syntax**

Run a YAML parser or GitHub Actions linter locally and inspect `gh workflow list` after pushing.
Expected: workflows parse and branch/environment mappings are distinct.

**Step 5: Document operations and rollback**

Document normal promotion, manual deploy commands, Supabase resume behavior, migration ordering, rollback by commit SHA, and the rule against production data in homologation.

**Step 6: Commit**

```bash
git add .github/workflows README.md
git commit -m "ci: deploy homologation and production by branch"
```

### Task 7: Publish and perform end-to-end verification

**Files:**
- No additional tracked changes expected

**Step 1: Scan for leaked secrets**

Run: `git diff main...HEAD` and a repository secret scan.
Expected: no database password, JWT secret, Supabase key, GCP credential, or access token is tracked.

**Step 2: Run the full test/build suite**

Run backend tests plus frontend and console tests/builds.
Expected: all checks pass.

**Step 3: Push the branch**

Run: `git push -u origin homologacao`
Expected: remote `homologacao` exists and triggers only homologation automation.

**Step 4: Perform smoke tests**

Validate the homologation frontend, backend health, login with a test user, a harmless database write/read, and logs. Confirm production URLs and production data remain unchanged.

**Step 5: Configure branch protection**

Require pull requests and passing checks for `main`; prevent accidental force pushes/deletion where repository settings allow it.

**Step 6: Record final resource inventory**

Report Supabase organization/project reference, Cloud Run service URL, Netlify URL, GitHub Environment names, test results, and any remaining manual approval requirement without exposing secrets.
