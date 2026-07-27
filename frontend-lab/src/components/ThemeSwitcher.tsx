import { THEMES, useTheme, type ThemeId } from "../lib/theme";

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="border-t border-border px-3 py-3">
      <div className="mb-2 text-xs uppercase tracking-wide text-text-muted">Color lab</div>
      <div className="flex flex-col gap-1">
        {THEMES.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTheme(t.id as ThemeId)}
            className={[
              "flex items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs",
              theme === t.id
                ? "bg-surface-3 text-text-primary"
                : "text-text-secondary hover:bg-surface-2 hover:text-text-primary",
            ].join(" ")}
          >
            <span
              className="size-2.5 shrink-0 rounded-full"
              style={{ background: t.swatch }}
              aria-hidden
            />
            <span className="flex-1">
              <span className="block font-medium">{t.label}</span>
              <span className="text-text-muted">{t.hint}</span>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
