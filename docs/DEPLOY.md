# Deploy SelfPI

Production layout:

1. **Frontend** → Vercel (Vite app in `frontend/`) + your **custom domain**
2. **Backend** → **AWS ECS Fargate** (repo-root `Dockerfile`) — see `infra/aws/`
3. **MongoDB** → [Atlas](https://www.mongodb.com/atlas)

Local demo (`make` / `make reset`) is separate. Keep `INCLUDE_DEMO_APIS=false` in prod.

---

## 1. Frontend (Vercel + custom domain)

1. Import the repo → **Root Directory:** `frontend` → Deploy.
2. Vercel → Project → **Domains** → add your domain (DNS as Vercel instructs).
3. After the API is up, set:

```bash
VITE_API_URL=https://YOUR-CLOUDFRONT-OR-API-HOST
```

No trailing slash. Redeploy — `VITE_*` is compile-time.

Use the **custom domain** (e.g. `https://selfpi.dev`) everywhere you mean “the product URL”, not `*.vercel.app`.

`frontend/vercel.json` rewrites SPA routes to `index.html`.

---

## 2. MongoDB Atlas

1. Create a free/shared cluster + DB user.
2. Network access: allow your host’s IPs (or `0.0.0.0/0` while Fargate has a public IP — tighten later).
3. Connection string:

```bash
MONGODB_URI=mongodb+srv://USER:PASS@CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=selfpi
```

Paste secrets only into Terraform / AWS Secrets Manager — never git.

---

## 3. Backend (AWS ECS Fargate)

Full walkthrough: [`infra/aws/README.md`](../infra/aws/README.md).

Summary:

```bash
cd infra/aws
cp terraform.tfvars.example terraform.tfvars
# frontend_url = "https://YOUR-CUSTOM-DOMAIN"
terraform init
terraform apply -var='desired_count=0'   # until an image exists in ECR
# push image (GitHub Actions or docker push)
terraform apply -var='desired_count=1'
terraform output api_url                 # → VITE_API_URL + GitHub App URLs
```

Stack: **ECR → Fargate → ALB → CloudFront (HTTPS)**. CloudFront gives you HTTPS without putting a cert on the API domain (required for Secure cookies from the Vercel HTTPS site).

### Env (set via Terraform → Secrets Manager / task env)

| Variable | Notes |
|----------|--------|
| `ENV` | `production` |
| `MONGODB_URI` / `MONGODB_DB` | Atlas |
| `CORS_ORIGINS` / `FRONTEND_URL` | Your **custom Vercel domain** |
| `GITHUB_OAUTH_REDIRECT_URI` | `https://<cloudfront>/auth/github/callback` (Terraform sets this) |
| `SESSION_SECRET` | Long random string |
| `GITHUB_APP_*` / OAuth client | From the GitHub App |
| `GITHUB_APP_INSTALLATION_ID` | Leave empty (multi-user installs) |
| `INCLUDE_DEMO_APIS` | `false` |

CI: [`.github/workflows/deploy-api.yml`](../.github/workflows/deploy-api.yml) builds/pushes to ECR and rolls the ECS service on pushes to `main` that touch `backend/**` or `Dockerfile`.

---

## 4. GitHub App public URLs

Use the CloudFront API origin from `terraform output`:

- **Callback URL:** `…/auth/github/callback`
- **Setup URL:** `…/auth/github/installed`

Permissions: Contents R/W, Pull requests R/W, Metadata R. Make the App public if others should install it.

---

## 5. Smoke checklist

1. `curl "$(cd infra/aws && terraform output -raw api_url)/health"` → `{"status":"ok"}`
2. Open your **custom domain** → Continue with GitHub → `/auth/callback`
3. Settings → Install SelfPI → Connect repo → Dashboard APIs / Check now

If login works but later calls are logged out: `CORS_ORIGINS` / `FRONTEND_URL` must match the exact custom domain (scheme + host), and `ENV=production`.

---

## Local vs demo

| Command | Effect |
|---------|--------|
| `make` | Local API + UI + portable mongod |
| `make reset` | Clean prod-style seed |
| `make reset-demo` / `make seed-demo` | Stripe demo harness only |

Do not enable the demo harness in production.

---

## Alternatives

Railway / Fly / Render also run the same `Dockerfile`. Prefer Fargate when you want an AWS/resume-standard container story; see `infra/aws/`.
