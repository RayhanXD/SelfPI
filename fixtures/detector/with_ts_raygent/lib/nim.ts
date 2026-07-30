const NIM_BASE_URL = "https://integrate.api.nvidia.com/v1";

export async function nimChat(messages: { role: string; content: string }[]) {
  const res = await fetch(`${NIM_BASE_URL}/chat/completions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.NIM_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ model: "meta/llama-3.1-8b-instruct", messages }),
  });
  return res.json();
}
