"use client";

import { useState } from "react";
import { apiBase, loginUser, registerUser, sendOtp, verifyOtp } from "../../../../lib/api";

type Mode = "login" | "register";
type RegisterStep = "details" | "otp" | "password";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function LoginForm({ consoleHref }: { consoleHref: string }) {
  const [mode, setMode] = useState<Mode>("login");
  const [step, setStep] = useState<RegisterStep>("details");

  // Form states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [fullName, setFullName] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [verificationToken, setVerificationToken] = useState("");

  // Status & error states
  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  function clearErrors() {
    setServerError(null);
    setFieldErrors({});
  }

  // --- Login Submit ---
  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    clearErrors();

    const errs: Record<string, string> = {};
    const trimmed = email.trim();
    if (!trimmed) errs.email = "ایمیل را وارد کنید.";
    else if (!EMAIL_RE.test(trimmed)) errs.email = "قالب ایمیل معتبر نیست.";
    if (!password) errs.password = "رمز عبور را وارد کنید.";
    else if (password.length < 8) errs.password = "رمز عبور باید حداقل ۸ نویسه باشد.";

    if (Object.keys(errs).length > 0) {
      setFieldErrors(errs);
      return;
    }

    setLoading(true);
    try {
      await loginUser({ email: trimmed, password });
      window.location.href = consoleHref;
    } catch (err: unknown) {
      setServerError(err instanceof Error ? err.message : "خطا در ورود به حساب");
    } finally {
      setLoading(false);
    }
  }

  // --- Register Step 1: Send OTP ---
  async function handleSendOtp(e: React.FormEvent) {
    e.preventDefault();
    clearErrors();

    const errs: Record<string, string> = {};
    const trimmedEmail = email.trim();
    const trimmedName = fullName.trim();

    if (!trimmedName) errs.fullName = "نام و نام خانوادگی را وارد کنید.";
    if (!trimmedEmail) errs.email = "ایمیل را وارد کنید.";
    else if (!EMAIL_RE.test(trimmedEmail)) errs.email = "قالب ایمیل معتبر نیست.";

    if (Object.keys(errs).length > 0) {
      setFieldErrors(errs);
      return;
    }

    setLoading(true);
    try {
      await sendOtp({ email: trimmedEmail, full_name: trimmedName });
      setStep("otp");
    } catch (err: unknown) {
      setServerError(err instanceof Error ? err.message : "خطا در ارسال کد تأیید");
    } finally {
      setLoading(false);
    }
  }

  // --- Register Step 2: Verify OTP ---
  async function handleVerifyOtp(e: React.FormEvent) {
    e.preventDefault();
    clearErrors();

    const code = otpCode.trim();
    if (!code || code.length !== 6) {
      setFieldErrors({ otp: "کد تأیید ۶ رقمی را به صورت کامل وارد کنید." });
      return;
    }

    setLoading(true);
    try {
      const res = await verifyOtp({ email: email.trim(), code });
      setVerificationToken(res.verification_token);
      setStep("password");
    } catch (err: unknown) {
      setServerError(err instanceof Error ? err.message : "کد تأیید نامعتبر یا منقضی شده است");
    } finally {
      setLoading(false);
    }
  }

  // --- Register Step 3: Set Password & Create Account ---
  async function handleCompleteRegistration(e: React.FormEvent) {
    e.preventDefault();
    clearErrors();

    const errs: Record<string, string> = {};
    if (!password) errs.password = "رمز عبور را وارد کنید.";
    else if (password.length < 8) errs.password = "رمز عبور باید حداقل ۸ نویسه باشد.";

    if (password !== passwordConfirm) {
      errs.passwordConfirm = "رمز عبور و تکرار آن یکسان نیستند.";
    }

    if (Object.keys(errs).length > 0) {
      setFieldErrors(errs);
      return;
    }

    setLoading(true);
    try {
      await registerUser({
        email: email.trim(),
        full_name: fullName.trim(),
        password,
        password_confirmation: passwordConfirm,
        verification_token: verificationToken,
      });
      window.location.href = consoleHref;
    } catch (err: unknown) {
      setServerError(err instanceof Error ? err.message : "خطا در ایجاد حساب کاربری");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* Header title depending on mode and step */}
      <div>
        <h1>
          {mode === "login"
            ? "ورود به حساب"
            : step === "details"
              ? "ثبت‌نام در سندباکس"
              : step === "otp"
                ? "تأیید ایمیل"
                : "تعیین رمز عبور"}
        </h1>
        <p className="mt2">
          {mode === "login"
            ? "برای مدیریت پروژه‌ها و آداپتورها وارد شوید."
            : step === "details"
              ? "اطلاعات خود را برای دریافت کد تأیید وارد کنید."
              : step === "otp"
                ? `کد ۶ رقمی ارسال‌شده به ${email} را وارد کنید.`
                : "رمز عبور خود را برای تکمیل ثبت‌نام تنظیم کنید."}
        </p>
      </div>

      {serverError && (
        <div role="alert" className="field__err">
          {serverError}
        </div>
      )}

      {/* Mode: Login */}
      {mode === "login" && (
        <>
          <form onSubmit={handleLogin} noValidate className="grid gap-4">
            <Fieldset
              id="email"
              label="ایمیل"
              error={fieldErrors.email}
              value={email}
              onChange={(v) => {
                setEmail(v);
                if (fieldErrors.email) setFieldErrors((e) => ({ ...e, email: "" }));
              }}
              type="email"
              placeholder="name@company.com"
              autoComplete="email"
            />
            <Fieldset
              id="password"
              label="رمز عبور"
              error={fieldErrors.password}
              value={password}
              onChange={(v) => {
                setPassword(v);
                if (fieldErrors.password) setFieldErrors((e) => ({ ...e, password: "" }));
              }}
              type="password"
              placeholder="حداقل ۸ نویسه"
              autoComplete="current-password"
            />
            <button
              type="submit"
              disabled={loading}
              className="btn btn--primary btn--block"
            >
              {loading ? "در حال بررسی..." : "ورود به حساب"}
            </button>
          </form>

          <div className="flex items-center gap-3 my-4 small muted">
            <span className="divider flex-1" />
            <span>یا ورود با</span>
            <span className="divider flex-1" />
          </div>

          <div className="grid gap-2.5">
            <button
              type="button"
              onClick={() => {
                window.location.href = `${apiBase}/api/v1/auth/oauth/github`;
              }}
              className="btn btn--secondary btn--block"
            >
              <svg width="19" height="19" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" className="shrink-0">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
              </svg>
              <span>ورود با حساب گیت‌هاب</span>
            </button>

            <button
              type="button"
              onClick={() => {
                window.location.href = `${apiBase}/api/v1/auth/oauth/google`;
              }}
              className="btn btn--secondary btn--block"
            >
              <svg width="19" height="19" viewBox="0 0 24 24" aria-hidden="true" className="shrink-0">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335" />
              </svg>
              <span>ورود با حساب گوگل</span>
            </button>
          </div>

          <p className="mt-6 small muted">
            حساب کاربری ندارید؟{" "}
            <button
              type="button"
              onClick={() => {
                setMode("register");
                setStep("details");
                clearErrors();
              }}
              className="btn btn--ghost btn--sm"
            >
              ثبت‌نام کنید
            </button>
          </p>
        </>
      )}

      {/* Mode: Register */}
      {mode === "register" && (
        <div>
          {/* Step 1: Details */}
          {step === "details" && (
            <form onSubmit={handleSendOtp} noValidate className="grid gap-4">
              <Fieldset
                id="fullName"
                label="نام و نام خانوادگی"
                error={fieldErrors.fullName}
                value={fullName}
                onChange={(v) => {
                  setFullName(v);
                  if (fieldErrors.fullName) setFieldErrors((e) => ({ ...e, fullName: "" }));
                }}
                type="text"
                placeholder="مثلاً علی رضایی"
                autoComplete="name"
              />
              <Fieldset
                id="email"
                label="ایمیل"
                error={fieldErrors.email}
                value={email}
                onChange={(v) => {
                  setEmail(v);
                  if (fieldErrors.email) setFieldErrors((e) => ({ ...e, email: "" }));
                }}
                type="email"
                placeholder="name@company.com"
                autoComplete="email"
              />
              <button
                type="submit"
                disabled={loading}
                className="btn btn--primary btn--block"
              >
                {loading ? "در حال ارسال کد..." : "دریافت کد تأیید ایمیل"}
              </button>
            </form>
          )}

          {/* Step 2: OTP */}
          {step === "otp" && (
            <form onSubmit={handleVerifyOtp} noValidate className="grid gap-4">
              <div className="field">
                <label htmlFor="otpCode" className="field__label">
                  کد تأیید ۶ رقمی
                </label>
                <input
                  id="otpCode"
                  value={otpCode}
                  onChange={(e) => {
                    setOtpCode(e.target.value);
                    if (fieldErrors.otp) setFieldErrors((e) => ({ ...e, otp: "" }));
                  }}
                  dir="ltr"
                  maxLength={6}
                  placeholder="------"
                  className="input mono text-center text-xl tracking-[0.4em]"
                  autoFocus
                />
                {fieldErrors.otp && (
                  <p role="alert" className="field__err">
                    {fieldErrors.otp}
                  </p>
                )}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn btn--primary btn--block"
              >
                {loading ? "در حال تأیید..." : "تأیید ایمیل و ادامه"}
              </button>

              <button
                type="button"
                onClick={() => {
                  setStep("details");
                  clearErrors();
                }}
                className="btn btn--ghost btn--block"
              >
                ویرایش نام یا ایمیل
              </button>
            </form>
          )}

          {/* Step 3: Password */}
          {step === "password" && (
            <form onSubmit={handleCompleteRegistration} noValidate className="grid gap-4">
              <Fieldset
                id="password"
                label="رمز عبور"
                error={fieldErrors.password}
                value={password}
                onChange={(v) => {
                  setPassword(v);
                  if (fieldErrors.password) setFieldErrors((e) => ({ ...e, password: "" }));
                }}
                type="password"
                placeholder="حداقل ۸ نویسه"
                autoComplete="new-password"
                autoFocus
              />
              <Fieldset
                id="passwordConfirm"
                label="تکرار رمز عبور"
                error={fieldErrors.passwordConfirm}
                value={passwordConfirm}
                onChange={(v) => {
                  setPasswordConfirm(v);
                  if (fieldErrors.passwordConfirm) setFieldErrors((e) => ({ ...e, passwordConfirm: "" }));
                }}
                type="password"
                placeholder="تکرار همان رمز عبور"
                autoComplete="new-password"
              />
              <button
                type="submit"
                disabled={loading}
                className="btn btn--primary btn--block"
              >
                {loading ? "در حال ثبت‌نام..." : "تکمیل ثبت‌نام و ورود"}
              </button>
            </form>
          )}

          <p className="mt-6 small muted">
            قبلاً ثبت‌نام کرده‌اید؟{" "}
            <button
              type="button"
              onClick={() => {
                setMode("login");
                clearErrors();
              }}
              className="btn btn--ghost btn--sm"
            >
              وارد شوید
            </button>
          </p>
        </div>
      )}
    </>
  );
}

function Fieldset({
  id,
  label,
  error,
  value,
  onChange,
  ...rest
}: {
  id: string;
  label: string;
  error?: string;
  value: string;
  onChange: (value: string) => void;
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange" | "id">) {
  const errorId = `${id}-error`;
  return (
    <div className="field">
      <label htmlFor={id} className="field__label">
        {label}
      </label>
      <input
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        dir={rest.type === "email" || rest.type === "password" ? "ltr" : "rtl"}
        aria-invalid={error ? true : undefined}
        aria-describedby={errorId}
        className="input"
        {...rest}
      />
      {error && (
        <p id={errorId} role="alert" className="field__err">
          {error}
        </p>
      )}
    </div>
  );
}
