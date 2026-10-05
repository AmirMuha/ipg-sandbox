import type { ReactNode } from "react";

export const metadata = {
  title: "IPG Sandbox",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return children;
}
