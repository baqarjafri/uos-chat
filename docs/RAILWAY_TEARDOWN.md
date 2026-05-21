# Railway takedown checklist

Use this after screenshots and the new README are pushed to GitHub.

## 1. Log in to Railway

```bash
npx @railway/cli login
npx @railway/cli whoami
```

## 2. List projects and services

```bash
npx @railway/cli list
```

Identify services for **uos-chat** (typically: PostgreSQL, backend, frontend).

## 3. Delete services (recommended order)

Delete in the Railway dashboard (**Project → Service → Settings → Delete Service**) or via CLI:

1. **Frontend** (`ai-uos` or similar)
2. **Backend** API service
3. **PostgreSQL** database (export a backup first if you need data)

> Deleting PostgreSQL is irreversible. Export via Railway dashboard if you want conversation/lead analytics.

## 4. Remove custom domains (if any)

Project → Settings → Domains → remove `*.up.railway.app` aliases you no longer need.

## 5. Verify takedown

```powershell
Invoke-WebRequest -Uri "https://ai-uos.up.railway.app" -Method Head -UseBasicParsing
```

Expect **404** or connection failure after DNS propagates.

## 6. Optional repo cleanup

After takedown, you may keep deployment docs for portfolio context or add a note at the top of `RAILWAY_DEPLOYMENT_GUIDE.md` pointing to `docs/DEMO_ARCHIVE.md`.

## 7. Make GitHub repository public

1. Open https://github.com/baqarjafri/uos-chat/settings
2. **General** → **Danger Zone** → **Change repository visibility** → **Public**
3. Confirm repository name and visibility

No secrets should be in the repo (verify `.env` is gitignored; only `.env.example` is tracked).
