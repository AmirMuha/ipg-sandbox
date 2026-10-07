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
    <div dir="rtl" className="mkt">
      <div className="wrap-m login-wrap">
        <div className="row-flex justify-between mb-6">
          <Link href={`/${locale}/home`} className="brand">
            <Image
              src="/logo.webp"
              alt="IPG Sandbox"
              width={32}
              height={32}
              className="object-contain shrink-0"
              priority
            />
            <span className="brand__name">سندباکس درگاه</span>
          </Link>
          <Link href={`/${locale}/home`} className="btn btn--ghost btn--sm">
            بازگشت به خانه
          </Link>
        </div>

        <main className="login-card">
          <LoginForm consoleHref={`/${locale}/console`} />
        </main>
      </div>
    </div>
  );
}
