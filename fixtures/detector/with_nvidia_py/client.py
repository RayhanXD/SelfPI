import openai

# Hosted NIM via OpenAI-compatible client
client = openai.OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="nvapi-test",
)
