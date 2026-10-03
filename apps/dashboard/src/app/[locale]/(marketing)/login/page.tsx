import type { Metadata } from "next";
import Link from "next/link";
import { setRequestLocale } from "next-intl/server";
import { LoginForm } from "./LoginForm";

export const metadata: Metadata = {
  title: "ورود | سندباکس درگاه",
  description: "ورود به حساب سندباکس درگاه برای مدیریت پروژه‌ها و آداپتورها.",
};

export default async function LoginPage({
  params: { locale },
}: {
  params: { locale: string };
}) {
  setRequestLocale(locale);

  return (
    <div
      dir="rtl"
      className="min-h-screen flex flex-col px-4 md:px-6 py-6 pb-12 gap-6"
    >
      <div className="flex items-center justify-between">
        <Link
          href={`/${locale}/home`}
          className="inline-flex items-center gap-2 font-display text-[17px] font-semibold"
        >
          <span className="w-7 h-7 grid place-items-center rounded-sm bg-accent text-accent-on shrink-0">
            <svg
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <rect x="2" y="5" width="20" height="14" rx="2" />
              <line x1="2" y1="10" x2="22" y2="10" />
              <line x1="6" y1="15" x2="6.01" y2="15" />
              <line x1="10" y1="15" x2="12" y2="15" />
            </svg>
          </span>
          سندباکس درگاه
        </Link>
        <Link href={`/${locale}/home`} className="text-sm text-muted hover:text-text">
          بازگشت به خانه
        </Link>
      </div>

      <main className="flex-1 grid place-items-center">
        <div className="w-full max-w-[420px] bg-surface border border-border rounded-lg p-8 shadow-raised animate-in">
          <div className="text-center mb-6">
            <h1 className="font-display text-xl font-semibold">ورود به حساب</h1>
            <p className="text-sm text-muted mt-2">
              برای مدیریت پروژه‌ها و آداپتورها وارد شوید.
            </p>
          </div>

          <LoginForm consoleHref={`/${locale}/transactions`} />

          <p className="mt-6 text-center text-sm text-muted">
            حساب کاربری ندارید؟{" "}
            <Link
              href={`/${locale}/pricing#plans`}
              className="text-accent-ink font-medium hover:underline"
            >
              پلن مناسب را ببینید
            </Link>
          </p>

          <p className="mt-5 flex items-start gap-2 px-4 py-3 bg-surface-subtle border border-border rounded-sm text-xs text-muted">
            <svg
              width="13"
              height="13"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="shrink-0 mt-0.5"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="16" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
            <span>
              این یک نمونه اولیه است: ورود بررسی می‌شود و سپس مستقیم به داشبورد تستی
              می‌روید.
            </span>
          </p>
        </div>
      </main>
    </div>
  );
}
