/** Export's `.page-head` — eyebrow, h1, lede, plus an optional badge row. */
export function PageHead({
  eyebrow,
  title,
  children,
  badges,
}: {
  eyebrow: string;
  title: string;
  children: React.ReactNode;
  badges?: React.ReactNode;
}) {
  return (
    <section className="w-full max-w-[1180px] mx-auto px-4 md:px-6 pt-14 md:pt-28 pb-8 md:pb-12">
      <div className="max-w-[640px]">
        <span className="inline-flex items-center gap-2 font-mono text-xs font-medium text-accent-ink">
          {eyebrow}
        </span>
        <h1 className="font-display text-[28px] md:text-[42px] font-semibold my-3">
          {title}
        </h1>
        <div className="text-xl text-text-2 leading-[1.62]">{children}</div>
        {badges && <div className="flex flex-wrap gap-3 mt-6">{badges}</div>}
      </div>
    </section>
  );
}

/** Export's `.badge` / `.badge-dot` / tone variants. */
export function Badge({
  children,
  tone = "neutral",
  dot = false,
}: {
  children: React.ReactNode;
  tone?: "neutral" | "success" | "warn" | "accent";
  dot?: boolean;
}) {
  const tones = {
    neutral: "border-border bg-bg text-text",
    success: "border-success-border bg-success-bg text-success-ink",
    warn: "border-warning-border bg-warning-bg text-warning-ink",
    accent: "border-accent bg-accent text-accent-on",
  };

  return (
    <span
      className={`inline-flex items-center gap-2 px-2 py-0.5 rounded-sm border font-mono text-xs font-medium leading-[1.7] ${tones[tone]}`}
    >
      {dot && <span className="w-1.5 h-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}
