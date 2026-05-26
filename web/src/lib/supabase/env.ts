type PublicSupabaseEnv = {
  url: string;
  publishableKey: string;
};

export function getPublicSupabaseEnv(): PublicSupabaseEnv {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

  const missing = [
    !url ? "NEXT_PUBLIC_SUPABASE_URL" : null,
    !publishableKey ? "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY" : null,
  ].filter(Boolean);

  if (missing.length > 0) {
    throw new Error(
      `Variables publiques Supabase manquantes: ${missing.join(", ")}. Consultez web/.env.example.`,
    );
  }

  return { url: url as string, publishableKey: publishableKey as string };
}
