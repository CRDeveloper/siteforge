import { getRequestConfig } from "next-intl/server";
import { cookies } from "next/headers";

const supportedLangs = JSON.parse(
  process.env.NEXT_PUBLIC_SUPPORTED_LANGS || '["en"]'
);
const defaultLang = process.env.NEXT_PUBLIC_DEFAULT_LANG || "en";

export default getRequestConfig(async () => {
  // Read locale from cookie, fallback to default
  const cookieStore = cookies();
  const cookieLang = cookieStore.get("sf_lang")?.value;
  const locale =
    cookieLang && supportedLangs.includes(cookieLang) ? cookieLang : defaultLang;

  const messages = (await import(`./locales/${locale}/common.json`)).default;

  return { locale, messages };
});
