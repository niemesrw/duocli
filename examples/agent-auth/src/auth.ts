import { createRemoteJWKSet, jwtVerify, type JWTPayload } from "jose";
import type { Request, Response, NextFunction } from "express";

// Duo OAuth 2.1 endpoints use: https://<sso-host>/oauth2/<app-id>/<endpoint>
// Set DUO_OAUTH_BASE to the full base URL, e.g.:
//   https://sso-xxx.sso.duosecurity.com/oauth2/YOURAPPID

// ─── Token fetching (client_credentials grant) ──────────────────────

interface TokenCache {
  accessToken: string;
  expiresAt: number;
}

const tokenCaches = new Map<string, TokenCache>();

export async function fetchAccessToken(
  clientId: string,
  clientSecret: string,
  oauthBase: string,
  scopes: string[] = ["agent:call"]
): Promise<string> {
  const cacheKey = `${clientId}@${oauthBase}`;
  const cached = tokenCaches.get(cacheKey);
  if (cached && cached.expiresAt > Date.now() + 30_000) {
    console.log(`[auth] Using cached token for ${clientId.slice(0, 8)}...`);
    return cached.accessToken;
  }

  const tokenUrl = `${oauthBase}/token`;
  console.log(`[auth] Requesting token from ${tokenUrl} for client ${clientId.slice(0, 8)}...`);

  const body = new URLSearchParams({
    grant_type: "client_credentials",
    client_id: clientId,
    client_secret: clientSecret,
    scope: scopes.join(" "),
  });

  const res = await fetch(tokenUrl, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });

  if (!res.ok) {
    const text = await res.text();
    console.error(`[auth] Token request FAILED (${res.status}): ${text}`);
    throw new Error(`Token request failed (${res.status}): ${text}`);
  }

  const json: any = await res.json();
  const accessToken = json.access_token;
  const expiresIn = json.expires_in || 3600;

  console.log(`[auth] Token acquired (expires in ${expiresIn}s, scopes: ${json.scope || "none"})`);

  tokenCaches.set(cacheKey, {
    accessToken,
    expiresAt: Date.now() + expiresIn * 1000,
  });

  return accessToken;
}

// ─── JWT validation middleware ───────────────────────────────────────

interface AuthMiddlewareOptions {
  requiredScopes?: string[];
}

export function createAuthMiddleware(
  oauthBase: string,
  options: AuthMiddlewareOptions = {}
) {
  const jwksUrl = new URL(`${oauthBase}/jwks`);
  const JWKS = createRemoteJWKSet(jwksUrl);
  const requiredScopes = options.requiredScopes || ["agent:call"];

  return async (req: Request, res: Response, next: NextFunction) => {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      res.status(401).json({ error: "Missing or invalid Authorization header" });
      return;
    }

    const token = authHeader.slice(7);
    console.log(`[auth] Validating JWT (${token.slice(0, 20)}...)`);

    try {
      const { payload } = await jwtVerify(token, JWKS, {
        issuer: oauthBase,
      });

      const tokenScopes = parseScopes(payload);
      const missing = requiredScopes.filter((s) => !tokenScopes.includes(s));
      if (missing.length > 0) {
        console.warn(`[auth] Insufficient scope — required: ${missing}, granted: ${tokenScopes}`);
        res.status(403).json({ error: "Insufficient scope", required: missing, granted: tokenScopes });
        return;
      }

      console.log(`[auth] Authenticated: sub=${payload.sub}, scopes=${tokenScopes.join(",")}`);

      (req as any).auth = {
        sub: payload.sub,
        clientId: payload.sub,
        scopes: tokenScopes,
        payload,
      };

      next();
    } catch (err: any) {
      console.error(`[auth] JWT validation FAILED: ${err.message}`);
      res.status(401).json({ error: "Invalid token", detail: err.message });
      return;
    }
  };
}

function parseScopes(payload: JWTPayload): string[] {
  const scope = (payload as any).scope;
  if (typeof scope === "string") return scope.split(" ").filter(Boolean);
  if (Array.isArray(scope)) return scope;
  return [];
}
