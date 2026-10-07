/** Export's `.section__head` — eyebrow, h2, lede, plus an optional badge row. */
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
    <section className="section wrap-m">
      <div className="section__head">
        <span className="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
        <p>{children}</p>
        {badges && <div className="row-flex mt-6">{badges}</div>}
      </div>
    </section>
  );
}

/** Export's `.badge` family, in the four tones the marketing pages use. */
export function Badge({
  children,
  tone = "neutral",
  dot = false,
}: {
  children: React.ReactNode;
  tone?: "neutral" | "success" | "warn" | "accent";
  dot?: boolean;
}) {
  // `neutral` maps to --refunded, NOT --failed. The design's --failed badge is
  // DASHED, which is its "did not happen" shape — correct for a failed delivery,
  // wrong for the plain counts and the free-plan chip that use this tone, where
  // it reads as a disabled control.
  const tones = {
    neutral: "badge--refunded",
    success: "badge--settled",
    warn: "badge--pending",
    accent: "badge--accent",
  };

  return (
    <span className={`badge ${tones[tone]}`}>
      {dot && <span className="badge__dot" aria-hidden="true" />}
      {children}
    </span>
  );
}
