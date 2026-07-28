"""Known third-party APIs — detection fingerprints + OpenAPI URLs.

Extend by appending an ApiCatalogEntry. Do not scatter vendor-specific
import/package strings through the pipeline (CLAUDE.md: extend by module).

Call-site surface maps live under languages/python/surfaces.py and are optional:
an API can be detected and watched before its SDK→operation_id map exists.

Entries with an empty `spec_url` are detectable but not auto-watched
(`watchable=False`); they surface in `unwatchable` so the UI can prompt for a
manual OpenAPI URL.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiCatalogEntry:
    id: str
    name: str
    spec_url: str
    # Pip / dependency names (matched case-insensitively in manifests).
    python_packages: tuple[str, ...]
    # Top-level import modules (`import X`, `from X import …`).
    python_imports: tuple[str, ...]

    @property
    def watchable(self) -> bool:
        """True when we have a fetchable OpenAPI URL."""
        return bool(self.spec_url.strip())


STRIPE_SPEC_URL = (
    "https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json"
)

_CATALOG: tuple[ApiCatalogEntry, ...] = (
    # ── Payments / fintech ──────────────────────────────────────────────
    ApiCatalogEntry(
        id="stripe",
        name="Stripe",
        spec_url=STRIPE_SPEC_URL,
        python_packages=("stripe",),
        python_imports=("stripe",),
    ),
    ApiCatalogEntry(
        id="plaid",
        name="Plaid",
        spec_url=(
            "https://raw.githubusercontent.com/plaid/plaid-openapi/master/2020-09-14.yml"
        ),
        python_packages=("plaid-python", "plaid"),
        python_imports=("plaid",),
    ),
    ApiCatalogEntry(
        id="square",
        name="Square",
        spec_url=(
            "https://raw.githubusercontent.com/square/connect-api-specification/"
            "master/api.json"
        ),
        python_packages=("squareup", "square"),
        python_imports=("square",),
    ),
    ApiCatalogEntry(
        id="paypal",
        name="PayPal",
        spec_url=(
            "https://raw.githubusercontent.com/paypal/paypal-rest-api-specifications/"
            "main/openapi/checkout_orders_v2.json"
        ),
        python_packages=("paypalrestsdk", "paypal-checkout-serversdk", "paypalhttp"),
        python_imports=("paypalrestsdk", "paypalcheckoutsdk", "paypalhttp"),
    ),
    ApiCatalogEntry(
        id="adyen",
        name="Adyen",
        spec_url=(
            "https://raw.githubusercontent.com/adyen/adyen-openapi/main/json/"
            "CheckoutService-v71.json"
        ),
        python_packages=("Adyen", "adyen"),
        python_imports=("Adyen",),
    ),
    ApiCatalogEntry(
        id="xero",
        name="Xero",
        spec_url=(
            "https://raw.githubusercontent.com/xeroapi/Xero-OpenAPI/master/"
            "xero_accounting.yaml"
        ),
        python_packages=("xero-python", "pyxero"),
        python_imports=("xero_python", "xero"),
    ),
    ApiCatalogEntry(
        id="braintree",
        name="Braintree",
        spec_url="",
        python_packages=("braintree",),
        python_imports=("braintree",),
    ),
    ApiCatalogEntry(
        id="chargebee",
        name="Chargebee",
        spec_url="",
        python_packages=("chargebee",),
        python_imports=("chargebee",),
    ),
    ApiCatalogEntry(
        id="recurly",
        name="Recurly",
        spec_url="",
        python_packages=("recurly",),
        python_imports=("recurly",),
    ),
    ApiCatalogEntry(
        id="razorpay",
        name="Razorpay",
        spec_url="",
        python_packages=("razorpay",),
        python_imports=("razorpay",),
    ),
    # ── AI / ML ─────────────────────────────────────────────────────────
    ApiCatalogEntry(
        id="openai",
        name="OpenAI",
        spec_url=(
            "https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml"
        ),
        python_packages=("openai",),
        python_imports=("openai",),
    ),
    ApiCatalogEntry(
        id="anthropic",
        name="Anthropic",
        spec_url="",
        python_packages=("anthropic",),
        python_imports=("anthropic",),
    ),
    ApiCatalogEntry(
        id="replicate",
        name="Replicate",
        spec_url="https://api.replicate.com/openapi.json",
        python_packages=("replicate",),
        python_imports=("replicate",),
    ),
    ApiCatalogEntry(
        id="mistral",
        name="Mistral AI",
        spec_url="https://docs.mistral.ai/openapi.yaml",
        python_packages=("mistralai",),
        python_imports=("mistralai",),
    ),
    ApiCatalogEntry(
        id="elevenlabs",
        name="ElevenLabs",
        spec_url="https://api.elevenlabs.io/openapi.json",
        python_packages=("elevenlabs",),
        python_imports=("elevenlabs",),
    ),
    ApiCatalogEntry(
        id="deepgram",
        name="Deepgram",
        spec_url=(
            "https://raw.githubusercontent.com/deepgram/deepgram-api-specs/main/"
            "openapi.yml"
        ),
        python_packages=("deepgram-sdk", "deepgram"),
        python_imports=("deepgram",),
    ),
    ApiCatalogEntry(
        id="firecrawl",
        name="Firecrawl",
        spec_url=(
            "https://raw.githubusercontent.com/firecrawl/firecrawl/main/apps/api/"
            "openapi.json"
        ),
        python_packages=("firecrawl-py", "firecrawl"),
        python_imports=("firecrawl",),
    ),
    ApiCatalogEntry(
        id="cohere",
        name="Cohere",
        spec_url="",
        python_packages=("cohere",),
        python_imports=("cohere",),
    ),
    ApiCatalogEntry(
        id="pinecone",
        name="Pinecone",
        spec_url="",
        python_packages=("pinecone", "pinecone-client"),
        python_imports=("pinecone",),
    ),
    ApiCatalogEntry(
        id="groq",
        name="Groq",
        spec_url="",
        python_packages=("groq",),
        python_imports=("groq",),
    ),
    ApiCatalogEntry(
        id="together",
        name="Together AI",
        spec_url="",
        python_packages=("together",),
        python_imports=("together",),
    ),
    ApiCatalogEntry(
        id="google-genai",
        name="Google Gemini",
        spec_url="",
        python_packages=("google-genai", "google-generativeai"),
        python_imports=("google.genai", "google.generativeai"),
    ),
    ApiCatalogEntry(
        id="huggingface",
        name="Hugging Face",
        spec_url="",
        python_packages=("huggingface_hub", "transformers"),
        python_imports=("huggingface_hub", "transformers"),
    ),
    ApiCatalogEntry(
        id="assemblyai",
        name="AssemblyAI",
        spec_url="",
        python_packages=("assemblyai",),
        python_imports=("assemblyai",),
    ),
    ApiCatalogEntry(
        id="voyage",
        name="Voyage AI",
        spec_url="",
        python_packages=("voyageai",),
        python_imports=("voyageai",),
    ),
    ApiCatalogEntry(
        id="perplexity",
        name="Perplexity",
        spec_url="",
        python_packages=("perplexityai", "perplexity"),
        python_imports=("perplexityai", "perplexity"),
    ),
    # ── Communications ──────────────────────────────────────────────────
    ApiCatalogEntry(
        id="twilio",
        name="Twilio",
        spec_url=(
            "https://raw.githubusercontent.com/twilio/twilio-oai/main/spec/json/"
            "twilio_api_v2010.json"
        ),
        python_packages=("twilio",),
        python_imports=("twilio",),
    ),
    ApiCatalogEntry(
        id="sendgrid",
        name="SendGrid",
        spec_url=(
            "https://raw.githubusercontent.com/twilio/sendgrid-oai/main/spec/json/"
            "tsg_mail_v3.json"
        ),
        python_packages=("sendgrid",),
        python_imports=("sendgrid",),
    ),
    ApiCatalogEntry(
        id="slack",
        name="Slack",
        spec_url=(
            "https://raw.githubusercontent.com/slackapi/slack-api-specs/master/"
            "web-api/slack_web_openapi_v2.json"
        ),
        python_packages=("slack_sdk", "slack-sdk", "slackclient"),
        python_imports=("slack_sdk", "slack"),
    ),
    ApiCatalogEntry(
        id="discord",
        name="Discord",
        spec_url=(
            "https://raw.githubusercontent.com/discord/discord-api-spec/main/"
            "specs/openapi.json"
        ),
        python_packages=("discord.py", "discord-py"),
        python_imports=("discord",),
    ),
    ApiCatalogEntry(
        id="intercom",
        name="Intercom",
        spec_url=(
            "https://raw.githubusercontent.com/Intercom/Intercom-OpenAPI/main/"
            "descriptions/2.11/api.intercom.io.yaml"
        ),
        python_packages=("python-intercom", "intercom-python"),
        python_imports=("intercom",),
    ),
    ApiCatalogEntry(
        id="resend",
        name="Resend",
        spec_url=(
            "https://raw.githubusercontent.com/resendlabs/resend-openapi/main/"
            "resend.yaml"
        ),
        python_packages=("resend",),
        python_imports=("resend",),
    ),
    ApiCatalogEntry(
        id="nylas",
        name="Nylas",
        spec_url="https://developer.nylas.com/docs/api/v3/openapi.yml",
        python_packages=("nylas",),
        python_imports=("nylas",),
    ),
    ApiCatalogEntry(
        id="mailgun",
        name="Mailgun",
        spec_url="",
        python_packages=("mailgun", "python-mailgun"),
        python_imports=("mailgun",),
    ),
    ApiCatalogEntry(
        id="postmark",
        name="Postmark",
        spec_url="",
        python_packages=("postmarker", "python-postmark"),
        python_imports=("postmarker",),
    ),
    ApiCatalogEntry(
        id="telegram",
        name="Telegram",
        spec_url="",
        python_packages=("python-telegram-bot", "telebot", "pyTelegramBotAPI"),
        python_imports=("telegram", "telebot"),
    ),
    # ── Developer platforms / git ───────────────────────────────────────
    ApiCatalogEntry(
        id="github",
        name="GitHub",
        spec_url=(
            "https://raw.githubusercontent.com/github/rest-api-description/main/"
            "descriptions/api.github.com/api.github.com.json"
        ),
        python_packages=("PyGithub", "pygithub"),
        python_imports=("github",),
    ),
    ApiCatalogEntry(
        id="circleci",
        name="CircleCI",
        spec_url="https://circleci.com/api/v2/openapi.json",
        python_packages=("circleci", "circleciapi"),
        python_imports=("circleci",),
    ),
    ApiCatalogEntry(
        id="gitlab",
        name="GitLab",
        spec_url="",
        python_packages=("python-gitlab",),
        python_imports=("gitlab",),
    ),
    ApiCatalogEntry(
        id="bitbucket",
        name="Bitbucket",
        spec_url="",
        python_packages=("atlassian-python-api",),
        python_imports=("atlassian",),
    ),
    # ── Productivity / SaaS ─────────────────────────────────────────────
    ApiCatalogEntry(
        id="asana",
        name="Asana",
        spec_url=(
            "https://raw.githubusercontent.com/Asana/developer-docs/master/defs/"
            "asana_oas.yaml"
        ),
        python_packages=("asana",),
        python_imports=("asana",),
    ),
    ApiCatalogEntry(
        id="box",
        name="Box",
        spec_url=(
            "https://raw.githubusercontent.com/box/box-openapi/main/openapi.json"
        ),
        python_packages=("boxsdk",),
        python_imports=("boxsdk",),
    ),
    ApiCatalogEntry(
        id="notion",
        name="Notion",
        spec_url=(
            "https://raw.githubusercontent.com/APIs-guru/openapi-directory/main/"
            "APIs/notion.com/1.0.0/openapi.yaml"
        ),
        python_packages=("notion-client",),
        python_imports=("notion_client",),
    ),
    ApiCatalogEntry(
        id="jira",
        name="Jira",
        spec_url=(
            "https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json"
        ),
        python_packages=("jira", "atlassian-python-api"),
        python_imports=("jira", "atlassian"),
    ),
    ApiCatalogEntry(
        id="trello",
        name="Trello",
        spec_url="https://developer.atlassian.com/cloud/trello/swagger.v3.json",
        python_packages=("py-trello", "trello"),
        python_imports=("trello",),
    ),
    ApiCatalogEntry(
        id="docusign",
        name="DocuSign",
        spec_url=(
            "https://raw.githubusercontent.com/docusign/OpenAPI-Specifications/"
            "master/esignature.rest.swagger-v2.1.json"
        ),
        python_packages=("docusign-esign",),
        python_imports=("docusign_esign",),
    ),
    ApiCatalogEntry(
        id="spotify",
        name="Spotify",
        spec_url=(
            "https://developer.spotify.com/reference/web-api/open-api-schema.yaml"
        ),
        python_packages=("spotipy",),
        python_imports=("spotipy",),
    ),
    ApiCatalogEntry(
        id="hubspot",
        name="HubSpot",
        spec_url="",
        python_packages=("hubspot-api-client",),
        python_imports=("hubspot",),
    ),
    ApiCatalogEntry(
        id="shopify",
        name="Shopify",
        spec_url="",
        python_packages=("ShopifyAPI", "shopifyapi"),
        python_imports=("shopify",),
    ),
    ApiCatalogEntry(
        id="airtable",
        name="Airtable",
        spec_url="",
        python_packages=("pyairtable", "airtable-python-wrapper"),
        python_imports=("pyairtable", "airtable"),
    ),
    ApiCatalogEntry(
        id="contentful",
        name="Contentful",
        spec_url="",
        python_packages=("contentful", "contentful_management"),
        python_imports=("contentful", "contentful_management"),
    ),
    ApiCatalogEntry(
        id="zendesk",
        name="Zendesk",
        spec_url="",
        python_packages=("zendesk", "zenpy"),
        python_imports=("zendesk", "zenpy"),
    ),
    ApiCatalogEntry(
        id="monday",
        name="Monday.com",
        spec_url="",
        python_packages=("monday",),
        python_imports=("monday",),
    ),
    ApiCatalogEntry(
        id="dropbox",
        name="Dropbox",
        spec_url="",
        python_packages=("dropbox",),
        python_imports=("dropbox",),
    ),
    ApiCatalogEntry(
        id="calendly",
        name="Calendly",
        spec_url="",
        python_packages=("calendly",),
        python_imports=("calendly",),
    ),
    ApiCatalogEntry(
        id="typeform",
        name="Typeform",
        spec_url="",
        python_packages=("typeform",),
        python_imports=("typeform",),
    ),
    ApiCatalogEntry(
        id="zoom",
        name="Zoom",
        spec_url="",
        python_packages=("zoomus",),
        python_imports=("zoomus",),
    ),
    # ── Auth / identity ─────────────────────────────────────────────────
    ApiCatalogEntry(
        id="auth0",
        name="Auth0",
        spec_url="",
        python_packages=("auth0-python",),
        python_imports=("auth0",),
    ),
    ApiCatalogEntry(
        id="okta",
        name="Okta",
        spec_url="",
        python_packages=("okta",),
        python_imports=("okta",),
    ),
    ApiCatalogEntry(
        id="clerk",
        name="Clerk",
        spec_url="",
        python_packages=("clerk-backend-api",),
        python_imports=("clerk_backend_api",),
    ),
    ApiCatalogEntry(
        id="workos",
        name="WorkOS",
        spec_url="",
        python_packages=("workos",),
        python_imports=("workos",),
    ),
    ApiCatalogEntry(
        id="stytch",
        name="Stytch",
        spec_url="",
        python_packages=("stytch",),
        python_imports=("stytch",),
    ),
    # ── Cloud / infra ───────────────────────────────────────────────────
    ApiCatalogEntry(
        id="digitalocean",
        name="DigitalOcean",
        spec_url=(
            "https://raw.githubusercontent.com/digitalocean/openapi/main/"
            "specification/DigitalOcean-public.v2.yaml"
        ),
        python_packages=("python-digitalocean",),
        python_imports=("digitalocean",),
    ),
    ApiCatalogEntry(
        id="cloudflare",
        name="Cloudflare",
        spec_url=(
            "https://raw.githubusercontent.com/cloudflare/api-schemas/main/"
            "openapi.json"
        ),
        python_packages=("cloudflare",),
        python_imports=("cloudflare",),
    ),
    ApiCatalogEntry(
        id="vercel",
        name="Vercel",
        spec_url="https://openapi.vercel.sh/",
        python_packages=("vercel",),
        python_imports=("vercel",),
    ),
    ApiCatalogEntry(
        id="netlify",
        name="Netlify",
        spec_url=(
            "https://raw.githubusercontent.com/netlify/open-api/master/swagger.yml"
        ),
        python_packages=("netlify",),
        python_imports=("netlify",),
    ),
    ApiCatalogEntry(
        id="supabase",
        name="Supabase",
        spec_url="https://api.supabase.com/api/v1-json",
        python_packages=("supabase",),
        python_imports=("supabase",),
    ),
    ApiCatalogEntry(
        id="docker",
        name="Docker Engine",
        spec_url=(
            "https://raw.githubusercontent.com/moby/moby/master/api/swagger.yaml"
        ),
        python_packages=("docker",),
        python_imports=("docker",),
    ),
    ApiCatalogEntry(
        id="docker-hub",
        name="Docker Hub",
        spec_url="https://docs.docker.com/reference/api/hub/latest.yaml",
        python_packages=("dockerhub",),
        python_imports=("dockerhub",),
    ),
    ApiCatalogEntry(
        id="kubernetes",
        name="Kubernetes",
        spec_url=(
            "https://raw.githubusercontent.com/kubernetes/kubernetes/release-1.30/"
            "api/openapi-spec/swagger.json"
        ),
        python_packages=("kubernetes",),
        python_imports=("kubernetes",),
    ),
    ApiCatalogEntry(
        id="aws",
        name="AWS",
        spec_url="",
        python_packages=("boto3", "botocore", "aioboto3"),
        python_imports=("boto3", "botocore", "aioboto3"),
    ),
    ApiCatalogEntry(
        id="azure",
        name="Azure",
        spec_url="",
        python_packages=("azure-identity", "azure-mgmt-resource", "azure-storage-blob"),
        python_imports=("azure",),
    ),
    ApiCatalogEntry(
        id="gcp",
        name="Google Cloud",
        spec_url="",
        python_packages=("google-cloud-storage", "google-cloud-bigquery", "google-api-python-client"),
        python_imports=("google.cloud", "googleapiclient"),
    ),
    ApiCatalogEntry(
        id="heroku",
        name="Heroku",
        spec_url="",
        python_packages=("heroku3",),
        python_imports=("heroku3",),
    ),
    ApiCatalogEntry(
        id="render",
        name="Render",
        spec_url="",
        python_packages=("render-sdk",),
        python_imports=("render_sdk",),
    ),
    ApiCatalogEntry(
        id="fly",
        name="Fly.io",
        spec_url="",
        python_packages=("flyio",),
        python_imports=("flyio",),
    ),
    ApiCatalogEntry(
        id="neon",
        name="Neon",
        spec_url="",
        python_packages=("neon-api", "neonize"),
        python_imports=("neon_api",),
    ),
    ApiCatalogEntry(
        id="planetscale",
        name="PlanetScale",
        spec_url="",
        python_packages=("planetscale",),
        python_imports=("planetscale",),
    ),
    ApiCatalogEntry(
        id="linode",
        name="Linode",
        spec_url="",
        python_packages=("linode_api4",),
        python_imports=("linode_api4",),
    ),
    ApiCatalogEntry(
        id="vultr",
        name="Vultr",
        spec_url="",
        python_packages=("vultr",),
        python_imports=("vultr",),
    ),
    # ── Data / search / observability ───────────────────────────────────
    # pymongo/motor talk to a MongoDB deployment — not the Atlas Admin OpenAPI.
    ApiCatalogEntry(
        id="mongodb",
        name="MongoDB",
        spec_url="",
        python_packages=("pymongo", "motor"),
        python_imports=("pymongo", "motor"),
    ),
    ApiCatalogEntry(
        id="mongodb-atlas",
        name="MongoDB Atlas Admin",
        spec_url=(
            "https://raw.githubusercontent.com/mongodb/openapi/main/openapi/v2.yaml"
        ),
        python_packages=("mongodb-atlas-api", "atlasapi"),
        python_imports=("atlasapi",),
    ),
    ApiCatalogEntry(
        id="algolia",
        name="Algolia",
        spec_url=(
            "https://raw.githubusercontent.com/algolia/api-clients-automation/main/"
            "specs/bundled/search.yml"
        ),
        python_packages=("algoliasearch",),
        python_imports=("algoliasearch",),
    ),
    ApiCatalogEntry(
        id="elasticsearch",
        name="Elasticsearch",
        spec_url=(
            "https://raw.githubusercontent.com/elastic/elasticsearch-specification/"
            "main/output/openapi/elasticsearch-serverless-openapi.json"
        ),
        python_packages=("elasticsearch",),
        python_imports=("elasticsearch",),
    ),
    ApiCatalogEntry(
        id="qdrant",
        name="Qdrant",
        spec_url=(
            "https://raw.githubusercontent.com/qdrant/qdrant/master/docs/redoc/"
            "master/openapi.json"
        ),
        python_packages=("qdrant-client",),
        python_imports=("qdrant_client",),
    ),
    ApiCatalogEntry(
        id="weaviate",
        name="Weaviate",
        spec_url=(
            "https://raw.githubusercontent.com/weaviate/weaviate/main/"
            "openapi-specs/schema.json"
        ),
        python_packages=("weaviate-client",),
        python_imports=("weaviate",),
    ),
    ApiCatalogEntry(
        id="datadog",
        name="Datadog",
        spec_url=(
            "https://raw.githubusercontent.com/DataDog/datadog-api-client-go/master/"
            ".generator/schemas/v1/openapi.yaml"
        ),
        python_packages=("datadog", "datadog-api-client"),
        python_imports=("datadog", "datadog_api_client"),
    ),
    ApiCatalogEntry(
        id="pagerduty",
        name="PagerDuty",
        spec_url=(
            "https://raw.githubusercontent.com/PagerDuty/api-schema/main/reference/"
            "REST/openapiv3.json"
        ),
        python_packages=("pdpyras", "pagerduty"),
        python_imports=("pdpyras", "pagerduty"),
    ),
    ApiCatalogEntry(
        id="launchdarkly",
        name="LaunchDarkly",
        spec_url="https://app.launchdarkly.com/api/v2/openapi.json",
        python_packages=("launchdarkly-server-sdk", "ldclient"),
        python_imports=("ldclient",),
    ),
    ApiCatalogEntry(
        id="sentry",
        name="Sentry",
        spec_url="",
        python_packages=("sentry-sdk",),
        python_imports=("sentry_sdk",),
    ),
    ApiCatalogEntry(
        id="posthog",
        name="PostHog",
        spec_url="",
        python_packages=("posthog",),
        python_imports=("posthog",),
    ),
    ApiCatalogEntry(
        id="mixpanel",
        name="Mixpanel",
        spec_url="",
        python_packages=("mixpanel",),
        python_imports=("mixpanel",),
    ),
    ApiCatalogEntry(
        id="amplitude",
        name="Amplitude",
        spec_url="",
        python_packages=("amplitude-analytics",),
        python_imports=("amplitude",),
    ),
    ApiCatalogEntry(
        id="segment",
        name="Segment",
        spec_url="",
        python_packages=("analytics-python", "segment-analytics-python"),
        python_imports=("analytics",),
    ),
    ApiCatalogEntry(
        id="chroma",
        name="Chroma",
        spec_url="",
        python_packages=("chromadb",),
        python_imports=("chromadb",),
    ),
    ApiCatalogEntry(
        id="milvus",
        name="Milvus",
        spec_url="",
        python_packages=("pymilvus",),
        python_imports=("pymilvus",),
    ),
    ApiCatalogEntry(
        id="redis",
        name="Redis",
        spec_url="",
        python_packages=("redis", "hiredis"),
        python_imports=("redis",),
    ),
    ApiCatalogEntry(
        id="snowflake",
        name="Snowflake",
        spec_url="",
        python_packages=("snowflake-connector-python", "snowflake-sqlalchemy"),
        python_imports=("snowflake",),
    ),
    ApiCatalogEntry(
        id="databricks",
        name="Databricks",
        spec_url="",
        python_packages=("databricks-sdk", "databricks-sql-connector"),
        python_imports=("databricks", "databricks.sql"),
    ),
    # ── Markets / data APIs ─────────────────────────────────────────────
    ApiCatalogEntry(
        id="coinbase",
        name="Coinbase",
        spec_url="",
        python_packages=("coinbase", "coinbase-advanced-py"),
        python_imports=("coinbase",),
    ),
    ApiCatalogEntry(
        id="binance",
        name="Binance",
        spec_url="",
        python_packages=("python-binance", "binance"),
        python_imports=("binance",),
    ),
    ApiCatalogEntry(
        id="alpaca",
        name="Alpaca",
        spec_url="",
        python_packages=("alpaca-py", "alpaca-trade-api"),
        python_imports=("alpaca",),
    ),
    ApiCatalogEntry(
        id="polygon",
        name="Polygon.io",
        spec_url="",
        python_packages=("polygon-api-client",),
        python_imports=("polygon",),
    ),
    ApiCatalogEntry(
        id="mapbox",
        name="Mapbox",
        spec_url="",
        python_packages=("mapbox", "mapbox-vector-tile"),
        python_imports=("mapbox",),
    ),
    ApiCatalogEntry(
        id="openweathermap",
        name="OpenWeatherMap",
        spec_url="",
        python_packages=("pyowm",),
        python_imports=("pyowm",),
    ),
    ApiCatalogEntry(
        id="newsapi",
        name="NewsAPI",
        spec_url="",
        python_packages=("newsapi-python",),
        python_imports=("newsapi",),
    ),
    ApiCatalogEntry(
        id="tavily",
        name="Tavily",
        spec_url="",
        python_packages=("tavily-python",),
        python_imports=("tavily",),
    ),
    # ── Social ──────────────────────────────────────────────────────────
    ApiCatalogEntry(
        id="reddit",
        name="Reddit",
        spec_url="",
        python_packages=("praw",),
        python_imports=("praw",),
    ),
    ApiCatalogEntry(
        id="twitter",
        name="Twitter / X",
        spec_url="",
        python_packages=("tweepy", "twitter-api-client"),
        python_imports=("tweepy",),
    ),
)


def all_entries() -> tuple[ApiCatalogEntry, ...]:
    return _CATALOG


def get_entry(api_id: str) -> ApiCatalogEntry | None:
    for entry in _CATALOG:
        if entry.id == api_id:
            return entry
    return None


def catalog_ids() -> frozenset[str]:
    return frozenset(e.id for e in _CATALOG)


def python_sdk_roots() -> tuple[str, ...]:
    """All import roots — used by the Python scanner prefilter."""
    roots: list[str] = []
    seen: set[str] = set()
    for entry in _CATALOG:
        for mod in entry.python_imports:
            # Prefilter matches top-level module names in source text.
            # Dotted imports like `google.cloud` still contribute `google`.
            root = mod.split(".", 1)[0]
            if root not in seen:
                seen.add(root)
                roots.append(root)
    return tuple(roots)
