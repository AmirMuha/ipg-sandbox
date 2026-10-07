"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { getMe, logoutUser, User, Project } from "../lib/api";

export function UserMenu({
  locale,
  active,
}: {
  locale: string;
  active: "home" | "providers" | "pricing" | "console";
}) {
  const isFa = locale === "fa";
  const [user, setUser] = useState<User | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let mounted = true;
    getMe()
      .then((data) => {
        if (mounted && data.user) {
          setUser(data.user);
          setProject(data.project);
        }
      })
      .catch(() => {
        // Unauthenticated or local single-project mode without auth session
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleLogout() {
    try {
      await logoutUser();
    } catch {
      // ignore network errors on logout
    }
    window.location.href = `/${locale}/login`;
  }

  // Holds the trigger's footprint so the topbar does not jump when the session lands.
  if (loading) {
    return <div className="w-8 h-8 shrink-0" />;
  }

  if (!user) {
    if (active === "console") {
      return (
        <div className="row-flex">
          <Link href={`/${locale}/login`} className="btn btn--secondary btn--sm">
            {isFa ? "ورود به حساب" : "Sign In"}
          </Link>
          <span className="hidden sm:inline">
            <Link href={`/${locale}/home`} className="btn btn--ghost btn--sm">
              {isFa ? "صفحه اصلی" : "Home"}
            </Link>
          </span>
        </div>
      );
    }

    return (
      <div className="row-flex">
        <span className="hidden sm:inline">
          <Link href={`/${locale}/login`} className="btn btn--ghost">
            {isFa ? "ورود" : "Login"}
          </Link>
        </span>
        <Link href={`/${locale}/login`} className="btn btn--secondary">
          {isFa ? "شروع رایگان" : "Start Free"}
        </Link>
      </div>
    );
  }

  const displayName = user.full_name || user.email.split("@")[0];
  const initial = (displayName[0] || "U").toUpperCase();
  const tierName =
    project?.tier === "team"
      ? isFa
        ? "تیم حرفه‌ای"
        : "Team"
      : isFa
        ? "توسعه‌دهنده"
        : "Developer";

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="btn btn--secondary btn--sm"
        aria-expanded={open}
        aria-haspopup="true"
      >
        <span className="brand__mark">{initial}</span>
        <span className="hidden sm:inline-block truncate max-w-[120px] font-medium">
          {displayName}
        </span>
        <svg
          className={`ic muted transition-transform duration-150 ${open ? "rotate-180" : ""}`}
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div
          dir={isFa ? "rtl" : "ltr"}
          className={`card absolute ${isFa ? "left-0" : "right-0"} mt-2 w-56 py-2 z-50`}
          role="menu"
        >
          <div className="px-4 py-2">
            <div className="small truncate font-semibold">{displayName}</div>
            <div className="small muted truncate">{user.email}</div>
            <div className="mt-1.5">
              <span className="badge badge--accent">{tierName}</span>
            </div>
          </div>

          <div className="divider" />

          <Link
            href={`/${locale}/console`}
            onClick={() => setOpen(false)}
            className="console-nav__link"
            role="menuitem"
          >
            <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
              <rect x="2" y="3" width="20" height="14" rx="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
            </svg>
            {isFa ? "کنسول تراکنش‌ها" : "Transactions Console"}
          </Link>

          <Link
            href={`/${locale}/settings`}
            onClick={() => setOpen(false)}
            className="console-nav__link"
            role="menuitem"
          >
            <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
            {isFa ? "تنظیمات و پلن" : "Settings & Plan"}
          </Link>

          {user.is_admin && (
            <Link
              href={`/${locale}/admin`}
              onClick={() => setOpen(false)}
              className="console-nav__link"
              role="menuitem"
              data-testid="admin-providers-nav"
            >
              <svg className="ic console-nav__lock" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              {isFa ? "مدیریت سامانه (مدیر)" : "Platform Admin"}
            </Link>
          )}

          <div className="divider my-1" />

          <button
            type="button"
            onClick={handleLogout}
            className="btn btn--danger btn--sm btn--block"
            role="menuitem"
          >
            <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            {isFa ? "خروج از حساب" : "Sign Out"}
          </button>
        </div>
      )}
    </div>
  );
}
