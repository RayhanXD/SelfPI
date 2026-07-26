interface EmptyStateProps {
  message: string;
}

export function EmptyState({ message }: EmptyStateProps) {
  return <p className="text-text-muted">{message}</p>;
}

interface ErrorStateProps {
  message: string;
}

export function ErrorState({ message }: ErrorStateProps) {
  return <p className="text-danger">{message}</p>;
}

interface SkeletonRowsProps {
  rows?: number;
  cols?: number;
}

export function SkeletonRows({ rows = 4, cols = 5 }: SkeletonRowsProps) {
  return (
    <div className="overflow-hidden rounded-md border border-border">
      <div className="border-b border-border bg-surface-2 px-3 py-2">
        <div className="h-3 w-40 animate-pulse rounded-sm bg-surface-3" />
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div
          key={r}
          className="flex gap-4 border-b border-border px-3 py-2.5 last:border-0"
        >
          {Array.from({ length: cols }).map((__, c) => (
            <div
              key={c}
              className="h-3 flex-1 animate-pulse rounded-sm bg-surface-2"
            />
          ))}
        </div>
      ))}
    </div>
  );
}
