import sentry_sdk
import posthog

sentry_sdk.init(dsn="https://example@sentry.io/1")
posthog.capture("user", "event")
