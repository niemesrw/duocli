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
import { fetchAccessToken } from "./auth.js";

const PORT = parseInt(process.env.ALICE_PORT || "4300", 10);
const OAUTH_BASE = process.env.DUO_OAUTH_BASE || "";
const CLIENT_ID = process.env.DUO_ALICE_CLIENT_ID || "";
const CLIENT_SECRET = process.env.DUO_ALICE_CLIENT_SECRET || "";

// ─── Agent Card ──────────────────────────────────────────────────────
const agentCard: AgentCard = {
  name: "Alice",
  description: "Demo agent that authenticates to Bob and sends messages via Duo OAuth 2.1.",
  protocolVersion: "0.3.0",
  version: "1.0.0",
  url: `http://localhost:${PORT}/a2a/jsonrpc`,
  skills: [
    {
      id: "ask-bob",
      name: "Ask Bob",
      description: "Authenticate to Bob via Duo and forward a message.",
      tags: ["demo", "auth"],
      examples: ["Ask Bob: Hello from Alice!"],
    },
  ],
  capabilities: { pushNotifications: false },
  defaultInputModes: ["text"],
  defaultOutputModes: ["text"],
};

// ─── Executor ────────────────────────────────────────────────────────
class AliceExecutor implements AgentExecutor {
  async execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void> {
    const { taskId, contextId, userMessage, task } = requestContext;

    if (!task) {
      eventBus.publish({
        kind: "task", id: taskId, contextId,
        status: { state: "submitted", timestamp: new Date().toISOString() },
        history: [userMessage],
      } as Task);
    }

    eventBus.publish({
      kind: "status-update", taskId, contextId,
      status: {
        state: "working",
        message: { role: "agent", parts: [{ kind: "text", text: "Authenticating to Duo and calling Bob..." }] },
        timestamp: new Date().toISOString(),
      },
      final: false,
    } as TaskStatusUpdateEvent);

    const textPart = userMessage.parts.find((p: any) => p.kind === "text");
    if (!textPart || textPart.kind !== "text") {
      return this.fail(taskId, contextId, eventBus, "No text provided.");
    }

    try {
      const token = await fetchAccessToken(CLIENT_ID, CLIENT_SECRET, OAUTH_BASE);

      const bobUrl = process.env.BOB_URL || `http://localhost:4400/a2a/jsonrpc`;
      const res = await fetch(bobUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: uuidv4(),
          method: "message/send",
          params: {
            message: {
              kind: "message",
              messageId: uuidv4(),
              role: "user",
              parts: [{ kind: "text", text: textPart.text }],
            },
          },
        }),
      });

      if (!res.ok) {
        const errText = await res.text();
        return this.fail(taskId, contextId, eventBus, `Bob returned HTTP ${res.status}: ${errText}`);
      }

      const json: any = await res.json();
      const bobTask = json.result;
      const bobText =
        bobTask?.artifacts?.[0]?.parts?.find((p: any) => p.kind === "text")?.text ||
        `Bob status: ${bobTask?.status?.state || "unknown"}`;

      eventBus.publish({
        kind: "artifact-update", taskId, contextId,
        artifact: { artifactId: uuidv4(), name: "bob-response", parts: [{ kind: "text", text: bobText }] },
        lastChunk: true,
      } as TaskArtifactUpdateEvent);

      eventBus.publish({
        kind: "status-update", taskId, contextId,
        status: { state: "completed", timestamp: new Date().toISOString() },
        final: true,
      } as TaskStatusUpdateEvent);

      eventBus.finished();
    } catch (err: any) {
      return this.fail(taskId, contextId, eventBus, `Error: ${err.message}`);
    }
  }

  private fail(taskId: string, contextId: string, eventBus: ExecutionEventBus, message: string) {
    eventBus.publish({
      kind: "status-update", taskId, contextId,
      status: { state: "failed", message: { role: "agent", parts: [{ kind: "text", text: message }] }, timestamp: new Date().toISOString() },
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
const executor = new AliceExecutor();
const requestHandler = new DefaultRequestHandler(agentCard, new InMemoryTaskStore(), executor);
const app = express();

// Alice is the entry point — no auth on her endpoints.
// She authenticates *outbound* to Bob using Duo OAuth.
app.use(`/${AGENT_CARD_PATH}`, agentCardHandler({ agentCardProvider: requestHandler }));
app.use("/a2a/jsonrpc", jsonRpcHandler({ requestHandler, userBuilder: UserBuilder.noAuthentication }));
app.use("/a2a/rest", restHandler({ requestHandler, userBuilder: UserBuilder.noAuthentication }));
app.get("/health", (_req, res) => res.json({ status: "ok", agent: "alice", oauthConfigured: !!OAUTH_BASE }));

app.listen(PORT, () => {
  console.log(`Alice A2A server running on http://localhost:${PORT}`);
  console.log(`OAuth base: ${OAUTH_BASE || "(not configured — auth disabled)"}`);
});

for (const signal of ["SIGTERM", "SIGINT"] as const) {
  process.on(signal, () => { console.log(`Received ${signal}, shutting down...`); process.exit(0); });
}
