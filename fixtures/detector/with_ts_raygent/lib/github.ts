const GITHUB_API_BASE = "https://api.github.com";

export async function fetchRepo(owner: string, repo: string, token?: string) {
  const headers: Record<string, string> = {
    Accept: "application/vnd.github+json",
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${GITHUB_API_BASE}/repos/${owner}/${repo}`, { headers });
  return res.json();
}
