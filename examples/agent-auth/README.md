# Agent Authentication with Duo OAuth 2.1

Two demo agents that authenticate to each other using Duo's OAuth 2.1 client_credentials grant. Built on Google's [A2A protocol](https://github.com/a2a-js/a2a-js).

**Alice** (port 4300) gets a JWT from Duo and calls **Bob** (port 4400). Bob validates the JWT via Duo's JWKS endpoint and returns the caller's identity.

## Prerequisites

1. A Duo account with SSO tier
2. An **OAuth 2.1 / OIDC** application created in the Duo Admin Panel
3. **Client Credentials** grant enabled under Client Flow Configuration
4. Two static clients created (e.g., `agent-alice` and `agent-bob`) with an `agent:call` scope

See the [blog post](https://ryandenime.substack.com/) for a full walkthrough with screenshots.

## Setup

```bash
npm install
```

Set environment variables:

```bash
# Full OAuth base URL (includes app ID)
export DUO_OAUTH_BASE="https://sso-xxx.sso.duosecurity.com/oauth2/YOURAPPID"

# Alice's credentials
export DUO_ALICE_CLIENT_ID="your-alice-client-id"
export DUO_ALICE_CLIENT_SECRET="your-alice-client-secret"
```

## Run

```bash
# Terminal 1 — start Bob
npm run bob

# Terminal 2 — start Alice
npm run alice
```

## Test

```bash
# Call Alice, who authenticates to Duo and calls Bob
curl -s -X POST http://localhost:4300/a2a/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"message/send","params":{"message":{"kind":"message","messageId":"t1","role":"user","parts":[{"kind":"text","text":"Hello Bob!"}]}}}' | python3 -m json.tool

# Call Bob directly without auth (should get 401)
curl -s http://localhost:4400/a2a/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"message/send","params":{"message":{"kind":"message","messageId":"t1","role":"user","parts":[{"kind":"text","text":"Hello"}]}}}'
```

## How it works

```
Alice                          Duo SSO                         Bob
  |                              |                              |
  |-- POST /token (creds) ------>|                              |
  |<-- JWT access_token ---------|                              |
  |                              |                              |
  |-- POST /a2a/jsonrpc ---------|----------------------------->|
  |   Authorization: Bearer JWT  |                              |
  |                              |    validate JWT via JWKS     |
  |                              |<----- GET /jwks -------------|
  |                              |-----> JWKS response -------->|
  |                              |                              |
  |<-----------------------------|---------- response ----------|
```

- `src/auth.ts` — Token fetcher (with caching) + Express JWT validation middleware
- `src/alice.ts` — Caller agent, fetches token from Duo, sends authenticated request
- `src/bob.ts` — Receiver agent, validates JWT, returns caller identity
