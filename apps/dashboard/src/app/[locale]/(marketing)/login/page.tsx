import type { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import { setRequestLocale } from "next-intl/server";
import { LoginForm } from "./LoginForm";

export const metadata: Metadata = {
  title: "ورود و ثبت‌نام | سندباکس درگاه",
  description: "ورود به حساب یا ثبت‌نام در سندباکس درگاه برای شبیه‌سازی درگاه‌های پرداخت.",
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
      className="min-h-screen flex flex-col px-4 md:px-6 py-6 pb-12 gap-6 bg-bg text-text"
    >
      <div className="flex items-center justify-between">
        <Link
          href={`/${locale}/home`}
          className="inline-flex items-center gap-2.5 font-display text-[17px] font-semibold text-text"
        >
          <Image
            src="/logo.webp"
            alt="IPG Sandbox"
            width={32}
            height={32}
            className="w-8 h-8 rounded-sm object-contain shrink-0"
            priority
          />
          سندباکس درگاه
        </Link>
        <Link href={`/${locale}/home`} className="text-sm text-muted hover:text-text">
          بازگشت به خانه
        </Link>
      </div>

      <main className="flex-1 grid place-items-center">
        <div className="w-full max-w-[420px] bg-surface border border-border rounded-lg p-8 shadow-raised animate-in">
          <LoginForm consoleHref={`/${locale}/console`} />
        </div>
      </main>
    </div>
  );
}
