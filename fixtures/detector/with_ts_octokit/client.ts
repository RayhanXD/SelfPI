import { Octokit } from "@octokit/rest";

export const gh = new Octokit({ auth: process.env.GITHUB_TOKEN });
