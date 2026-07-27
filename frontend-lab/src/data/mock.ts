import type { ApiSummary, ChangeDetail, ChangeSummary } from "../types";

export const MOCK_USER = {
  login: "rayhan",
  name: "Rayhan Mohammad",
  avatar_url: null as string | null,
};

export const MOCK_APIS: ApiSummary[] = [
  {
    id: "stripe-demo",
    name: "Stripe (demo)",
    current_version: "demo-2026.07.26",
    status: "breaking_change_unhandled",
    languages: ["python"],
    last_checked: "2026-07-26T23:23:56Z",
    open_change_count: 1,
    repo: "myorg/billing-app",
    mode: "demo",
  },
  {
    id: "stripe",
    name: "Stripe",
    current_version: "2026-06-24.dahlia",
    status: "up_to_date",
    languages: ["python"],
    last_checked: "2026-07-26T22:10:00Z",
    open_change_count: 0,
    repo: "myorg/billing-app",
    mode: "live",
  },
  {
    id: "twilio",
    name: "Twilio",
    current_version: "2026.05.12",
    status: "change_detected",
    languages: ["python"],
    last_checked: "2026-07-26T21:40:00Z",
    open_change_count: 1,
    repo: "myorg/billing-app",
    mode: "live",
  },
];

export const MOCK_CHANGES: ChangeSummary[] = [
  {
    id: "chg_source_pm",
    api_id: "stripe-demo",
    operation_id: "PostCharges",
    kind: "renamed_param",
    call_site_count: 3,
    status: "pr_open",
    pr: {
      number: 42,
      url: "https://github.com/myorg/billing-app/pull/42",
      state: "open",
      tests_passing: true,
      opened_at: "2026-07-26T23:24:10Z",
    },
    detected_at: "2026-07-26T23:23:56Z",
  },
  {
    id: "chg_twilio_sid",
    api_id: "twilio",
    operation_id: "CreateMessage",
    kind: "removed_field",
    call_site_count: 2,
    status: "detected",
    pr: null,
    detected_at: "2026-07-26T21:41:00Z",
  },
  {
    id: "chg_merged_example",
    api_id: "stripe",
    operation_id: "GetCustomers",
    kind: "value_deprecated",
    call_site_count: 1,
    status: "merged",
    pr: {
      number: 38,
      url: "https://github.com/myorg/billing-app/pull/38",
      state: "merged",
      tests_passing: true,
      opened_at: "2026-07-20T14:02:00Z",
    },
    detected_at: "2026-07-20T14:00:00Z",
  },
];

export const MOCK_REPOS = [
  "myorg/billing-app",
  "myorg/payments-service",
  "myorg/legacy-checkout",
];

export const MOCK_CHANGE_DETAIL: ChangeDetail = {
  id: "chg_source_pm",
  api_id: "stripe-demo",
  operation_id: "PostCharges",
  kind: "renamed_param",
  status: "pr_open",
  pr: {
    number: 42,
    url: "https://github.com/myorg/billing-app/pull/42",
    state: "open",
    tests_passing: true,
    opened_at: "2026-07-26T23:24:10Z",
  },
  detected_at: "2026-07-26T23:23:56Z",
  from_version: "demo-2026.07.25",
  to_version: "demo-2026.07.26",
  repo: "myorg/billing-app",
  detail: { from: "source", to: "payment_method" },
  explanation:
    "Stripe renamed `source` → `payment_method` on charge create. Updated 3 Python call sites to the new parameter.",
  patch_preview: `--- a/billing.py
+++ b/billing.py
@@ -12,7 +12,7 @@
 def charge_customer(customer_id, amount):
     return stripe.Charge.create(
         amount=amount,
         currency="usd",
-        source=customer_id,
+        payment_method=customer_id,
     )
`,
  spec_diff: {
    operation_id: "PostCharges",
    removed: ["source"],
    added: ["payment_method"],
    raw: ` operation PostCharges
-  source: string
+  payment_method: string`,
  },
  call_sites: [
    {
      file: "billing.py",
      span: { start_line: 16, end_line: 16 },
      language: "python",
      receiver: "stripe",
      path: ["Charge", "create"],
      invoked: true,
      operation_id: "PostCharges",
      args: [{ name: "source", kind: "keyword" }],
      snippet: 'stripe.Charge.create(amount=amount, currency="usd", source=customer_id)',
      source_layer: "structural",
      confidence: 0.94,
      in_comment: false,
    },
    {
      file: "webhooks/charges.py",
      span: { start_line: 48, end_line: 48 },
      language: "python",
      receiver: "stripe",
      path: ["Charge", "create"],
      invoked: true,
      operation_id: "PostCharges",
      args: [{ name: "source", kind: "keyword" }],
      snippet: "stripe.Charge.create(source=tok, amount=cents)",
      source_layer: "grep",
      confidence: 0.72,
      in_comment: false,
    },
    {
      file: "legacy/old_billing.py",
      span: { start_line: 102, end_line: 102 },
      language: "python",
      receiver: "stripe",
      path: ["Charge", "create"],
      invoked: true,
      operation_id: "PostCharges",
      args: [{ name: "source", kind: "keyword" }],
      snippet: "# stripe.Charge.create(source=…)",
      source_layer: "agent",
      confidence: 0.41,
      in_comment: true,
    },
  ],
};

/** Inbox count for sidebar — open / actionable only. */
export function mockInboxCount() {
  return MOCK_CHANGES.filter(
    (c) => c.status === "detected" || c.status === "scanning" || c.status === "pr_open",
  ).length;
}
