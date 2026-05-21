# Live demo archive

The public demo previously hosted at **https://ai-uos.up.railway.app** has been retired to reduce hosting cost and keep this repository as the canonical showcase.

## What replaced the live site

- Screenshots in [`docs/images/`](images/) — captured from production before takedown (May 2026)
- The README on GitHub — visual walkthrough of UI, architecture, and chat features
- Local run instructions in the root [README](../README.md#quick-start-local-development)

## Running the app locally

You need your own API keys (OpenAI + Anthropic) and a local PostgreSQL instance with pgvector. See the main README for step-by-step setup.

## Historical deployment

Railway deployment files remain in the repo for reference:

- `backend/Dockerfile.railway`, `frontend/Dockerfile.railway`
- `DEPLOYMENT_STRUCTURE.md`, `RAILWAY_DEPLOYMENT_GUIDE.md`, `PRE_DEPLOYMENT_CHECKLIST.md`

To remove Railway services entirely, follow [RAILWAY_TEARDOWN.md](RAILWAY_TEARDOWN.md).
