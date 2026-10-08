import { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { ApiKeysList } from "../../../../../components/api-keys/ApiKeysList";

export const metadata: Metadata = {
  title: "API Keys",
};

export default async function ApiKeysPage({
  params: { locale },
}: {
  params: { locale: string };
}) {
  return (
    <div className="max-w-5xl mx-auto py-8 px-4 stack-lg">
      <div>
        <h1 className="text-2xl font-bold">API Keys</h1>
        <p className="text-slate-500 mt-1">Manage programmatic access to your sandbox.</p>
      </div>

      <ApiKeysList />
    </div>
  );
}
