import express from "express";
import { v4 as uuidv4 } from "uuid";
import {
  AgentCard,
  Task,
  TaskStatusUpdateEvent,
  TaskArtifactUpdateEvent,
  AGENT_CARD_PATH,
} from "@a2a-js/sdk";
import {
  AgentExecutor,
  RequestContext,
  ExecutionEventBus,
  DefaultRequestHandler,
  InMemoryTaskStore,
} from "@a2a-js/sdk/server";
import {
  agentCardHandler,
  jsonRpcHandler,
  restHandler,
  UserBuilder,
} from "@a2a-js/sdk/server/express";
import { createAuthMiddleware } from "./auth.js";

const PORT = parseInt(process.env.BOB_PORT || "4400", 10);
const OAUTH_BASE = process.env.DUO_OAUTH_BASE || "";

// Module-level auth stash — single-threaded Node, so this is safe for the demo
let _lastAuth: { sub: string; clientId: string; scopes: string[] } | null = null;

// ─── Agent Card ──────────────────────────────────────────────────────
const agentCard: AgentCard = {
  name: "Bob",
  description: "Demo agent that echoes messages back with caller identity from JWT.",
  protocolVersion: "0.3.0",
  version: "1.0.0",
  url: `http://localhost:${PORT}/a2a/jsonrpc`,
  skills: [
    {
      id: "echo",
      name: "Echo",
      description: "Echoes back whatever was sent, along with the authenticated caller's identity.",
      tags: ["demo", "auth", "echo"],
      examples: ["Hello Bob!"],
    },
  ],
  capabilities: { pushNotifications: false },
  defaultInputModes: ["text"],
  defaultOutputModes: ["text"],
};

// ─── Executor ────────────────────────────────────────────────────────
class BobExecutor implements AgentExecutor {
  async execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void> {
    const { taskId, contextId, userMessage, task } = requestContext;

    if (!task) {
      eventBus.publish({
        kind: "task", id: taskId, contextId,
        status: { state: "submitted", timestamp: new Date().toISOString() },
        history: [userMessage],
      } as Task);
    }

    const textPart = userMessage.parts.find((p: any) => p.kind === "text");
    const inputText = textPart?.kind === "text" ? textPart.text : "(no text)";

    // Retrieve auth context stashed by the middleware
    const auth = _lastAuth;
    _lastAuth = null;

    const greeting = auth
      ? `Hello ${auth.sub}! I verified your identity via Duo (scopes: ${auth.scopes.join(", ")})`
      : "Hello stranger! You're unauthenticated — I don't know who you are.";

    const responseText = `${greeting}\nYou said: "${inputText}"`;

    eventBus.publish({
      kind: "artifact-update", taskId, contextId,
      artifact: { artifactId: uuidv4(), name: "echo-response", parts: [{ kind: "text", text: responseText }] },
      lastChunk: true,
    } as TaskArtifactUpdateEvent);

    eventBus.publish({
      kind: "status-update", taskId, contextId,
      status: { state: "completed", timestamp: new Date().toISOString() },
      final: true,
    } as TaskStatusUpdateEvent);

    eventBus.finished();
  }

  async cancelTask(taskId: string, eventBus: ExecutionEventBus): Promise<void> {
    eventBus.publish({
      kind: "status-update", taskId, contextId: "",
      status: { state: "canceled", timestamp: new Date().toISOString() },
      final: true,
    } as TaskStatusUpdateEvent);
    eventBus.finished();
  }
}

// ─── Server ──────────────────────────────────────────────────────────
const executor = new BobExecutor();
const requestHandler = new DefaultRequestHandler(agentCard, new InMemoryTaskStore(), executor);
const app = express();

const authMiddleware = OAUTH_BASE
  ? createAuthMiddleware(OAUTH_BASE, { requiredScopes: ["agent:call"] })
  : (_req: any, _res: any, next: any) => next();

app.use(`/${AGENT_CARD_PATH}`, agentCardHandler({ agentCardProvider: requestHandler }));

// Auth middleware → stash auth → JSON-RPC handler
app.use("/a2a/jsonrpc", authMiddleware, (req: any, _res: any, next: any) => {
  _lastAuth = req.auth || null;
  next();
}, jsonRpcHandler({ requestHandler, userBuilder: UserBuilder.noAuthentication }));

app.use("/a2a/rest", authMiddleware, restHandler({ requestHandler, userBuilder: UserBuilder.noAuthentication }));
app.get("/health", (_req, res) => res.json({ status: "ok", agent: "bob", oauthConfigured: !!OAUTH_BASE }));

app.listen(PORT, () => {
  console.log(`Bob A2A server running on http://localhost:${PORT}`);
  console.log(`OAuth base: ${OAUTH_BASE || "(not configured — auth disabled)"}`);
});

for (const signal of ["SIGTERM", "SIGINT"] as const) {
  process.on(signal, () => { console.log(`Received ${signal}, shutting down...`); process.exit(0); });
}
