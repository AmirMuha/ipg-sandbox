"use client";

import { useState } from "react";

/**
 * Login form from login.html.
 *
 * The engine has no auth backend (ENGINE_PROFILE=local runs one shared project
 * with no login), so this is the export's prototype behaviour verbatim: validate
 * in the browser, then go to the console. Inline errors on each field, cleared
 * on input, focus moved to the first invalid field — accessibility basics the
 * export already got right.
 */

type Field = "email" | "password";

const ERRORS = {
  emailRequired: "ایمیل را وارد کنید.",
  emailFormat: "قالب ایمیل معتبر نیست.",
  passwordShort: "رمز عبور باید حداقل ۸ نویسه باشد.",
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function LoginForm({ consoleHref }: { consoleHref: string }) {
  const [errors, setErrors] = useState<Partial<Record<Field, string>>>({});
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function validate() {
    const next: Partial<Record<Field, string>> = {};
    const trimmed = email.trim();
    if (!trimmed) next.email = ERRORS.emailRequired;
    else if (!EMAIL_RE.test(trimmed)) next.email = ERRORS.emailFormat;
    if (password.length < 8) next.password = ERRORS.passwordShort;
    return next;
  }

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next = validate();
    setErrors(next);

    const firstBad = (Object.keys(next) as Field[])[0];
    if (firstBad) {
      document.getElementById(firstBad)?.focus();
      return;
    }
    window.location.href = consoleHref;
  }

  return (
    <>
      <form onSubmit={submit} noValidate className="grid gap-4">
        <Fieldset
          id="email"
          label="ایمیل"
          error={errors.email}
          value={email}
          onChange={(v) => {
            setEmail(v);
            if (errors.email) setErrors((e) => ({ ...e, email: undefined }));
          }}
          type="email"
          placeholder="name@company.com"
          autoComplete="email"
        />
        <Fieldset
          id="password"
          label="رمز عبور"
          error={errors.password}
          value={password}
          onChange={(v) => {
            setPassword(v);
            if (errors.password)
              setErrors((e) => ({ ...e, password: undefined }));
          }}
          type="password"
          placeholder="حداقل ۸ نویسه"
          autoComplete="current-password"
        />
        <button
          type="submit"
          className="inline-flex items-center justify-center min-h-12 px-6 rounded-md bg-accent text-accent-on text-[17px] font-medium hover:bg-accent/92 active:bg-accent/86 transition-colors duration-fast ease-standard"
        >
          ورود به حساب
        </button>
      </form>

      <div className="flex items-center gap-3 my-2 text-xs text-muted">
        <span className="flex-1 h-px bg-border" />
        یا
        <span className="flex-1 h-px bg-border" />
      </div>

      <button
        type="button"
        onClick={() => {
          window.location.href = consoleHref;
        }}
        className="inline-flex items-center justify-center min-h-12 px-6 rounded-md border border-border bg-surface text-text text-[17px] font-medium hover:bg-surface-subtle transition-colors duration-fast ease-standard"
      >
        <svg
          width="17"
          height="17"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="ms-2"
          aria-hidden="true"
        >
          <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
        </svg>
        ورود با گیت‌هاب
      </button>
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
  id: Field;
  label: string;
  error?: string;
  value: string;
  onChange: (value: string) => void;
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange" | "id">) {
  const errorId = `${id}-error`;
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="text-sm font-medium">
        {label}
      </label>
      <input
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        dir="ltr"
        aria-invalid={error ? true : undefined}
        aria-describedby={errorId}
        className="w-full min-h-11 px-3 bg-surface border border-border rounded-sm text-sm text-text placeholder:text-muted transition-colors duration-fast ease-standard focus:border-accent focus:shadow-[0_0_0_3px_rgb(var(--accent)/0.1)]"
        {...rest}
      />
      <p id={errorId} role="alert" hidden={!error} className="text-xs text-danger-ink">
        {error}
      </p>
    </div>
  );
}
