"""Python SDK surface → OpenAPI operationId maps (per vendor).

Stripe is fully mapped for the v1 demo loop. Other catalog APIs may be
detected and watched before a surface map exists — call-site finding for
those is a no-op until entries are added here.
"""

from __future__ import annotations

# Stripe (v1 wedge — complete enough for createCharge rename demo)
STRIPE: dict[tuple[str, ...], str] = {
    ("Charge", "create"): "createCharge",
    ("Charge", "retrieve"): "retrieveCharge",
    ("Customer", "create"): "createCustomer",
    ("PaymentIntent", "create"): "createPaymentIntent",
}

# OpenAI — legacy 0.x SDK surfaces (WishBot-style) + common v1 names.
OPENAI: dict[tuple[str, ...], str] = {
    ("Audio", "transcribe"): "createTranscription",
    ("Audio", "translate"): "createTranslation",
    ("ChatCompletion", "create"): "createChatCompletion",
    ("Completion", "create"): "createCompletion",
    ("Image", "create"): "createImage",
    ("Embedding", "create"): "createEmbedding",
    ("Embeddings", "create"): "createEmbedding",
}

# Merge all vendor maps. Later vendors append here.
SURFACE_TO_OPERATION: dict[tuple[str, ...], str] = {
    **STRIPE,
    **OPENAI,
}
