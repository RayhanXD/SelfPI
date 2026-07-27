export function SettingsPage() {
  const rows = [
    { label: "GitHub App", value: "Configured" },
    { label: "Default base branch", value: "main" },
    { label: "Connected repo", value: "myorg/billing-app" },
    { label: "Scheduled watcher", value: "Every 300s" },
    { label: "Primary API", value: "stripe" },
    { label: "Languages", value: "python" },
  ];

  return (
    <div className="max-w-lg space-y-3">
      <p className="text-[13px] text-[#8a8a8a]">
        Workspace connection and runtime configuration.
      </p>
      <div className="overflow-hidden rounded-2xl border border-white/[0.07]">
        {rows.map((row, i) => (
          <div
            key={row.label}
            className={[
              "flex items-center justify-between gap-4 px-5 py-3.5 text-[13px]",
              i > 0 ? "border-t border-white/[0.06]" : "",
            ].join(" ")}
          >
            <dt className="text-[#8a8a8a]">{row.label}</dt>
            <dd className="truncate font-mono text-[12px] tracking-normal text-[#a8a8a8]">
              {row.value}
            </dd>
          </div>
        ))}
      </div>
    </div>
  );
}
