# SelfPI API — AWS ECS Fargate

Deploys the repo-root `Dockerfile` to **ECS Fargate** behind an **ALB**, with **CloudFront** in front for HTTPS (needed for GitHub OAuth cookies from a Vercel HTTPS frontend).

```
Vercel (custom domain)  →  CloudFront HTTPS  →  ALB  →  Fargate (FastAPI)
                              MongoDB Atlas
```

## Prerequisites

1. AWS account + IAM user/role that can manage ECR, ECS, ELB, CloudFront, IAM, Secrets Manager, CloudWatch Logs
2. [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.5
3. [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) configured (`aws sts get-caller-identity`)
4. MongoDB Atlas cluster + connection string
5. Docker **or** GitHub Actions (recommended) to build/push the image
6. Your Vercel **custom domain** ready (e.g. `https://selfpi.dev`) — use that, not `*.vercel.app`, for CORS / OAuth

## 1. Configure secrets

```bash
cd infra/aws
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars — set frontend_url to your custom domain
```

Example:

```hcl
frontend_url = "https://selfpi.dev"
cors_origins = "https://selfpi.dev"   # optional; defaults to frontend_url
```

## 2. Create infra (ECR first if the image is not pushed yet)

```bash
terraform init
# First image not in ECR yet? create registry + supporting pieces, keep tasks at 0:
terraform apply -var='desired_count=0'
```

Note `ecr_repository_url` and `api_url` from outputs.

## 3. Push an image

**Option A — GitHub Actions** (see `.github/workflows/deploy-api.yml`): add repo secrets `AWS_ROLE_ARN` (OIDC) or `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`, plus `AWS_REGION`. Push to `main` touching `backend/**` or `Dockerfile`.

**Option B — local Docker:**

```bash
AWS_REGION=us-east-1
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REPO=$(terraform output -raw ecr_repository_url)

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com"

docker build -t "$REPO:latest" -f ../../Dockerfile ../..
docker push "$REPO:latest"
```

Then scale up:

```bash
terraform apply -var='desired_count=1'
```

## 4. Wire frontend + GitHub App

| Place | Value |
|-------|--------|
| Vercel `VITE_API_URL` | `terraform output -raw api_url` |
| Vercel domain | your custom domain (already on the frontend) |
| GitHub App **Callback URL** | `terraform output -raw github_oauth_callback` |
| GitHub App **Setup URL** | `terraform output -raw github_setup_url` |
| Atlas Network | allow `0.0.0.0/0` (or tighten to NAT later) |

Redeploy the Vercel frontend after setting `VITE_API_URL`.

## 5. Smoke

```bash
curl "$(terraform output -raw api_url)/health"
# → {"status":"ok"}
```

Open your custom domain → Login with GitHub.

## Cost (approx, us-east-1 hobby)

- Fargate 0.5 vCPU / 1 GB ≈ a few dollars/day if left on 24/7 — stop the service when idle: `aws ecs update-service --desired-count 0 …`
- ALB ≈ $16+/mo while running
- CloudFront + ECR + Secrets Manager = small

Destroy when done: `terraform destroy`.

## Updating secrets

Edit `terraform.tfvars`, then `terraform apply`. Force a new deployment so tasks pick up Secrets Manager:

```bash
aws ecs update-service --cluster selfpi --service selfpi-api --force-new-deployment
```
