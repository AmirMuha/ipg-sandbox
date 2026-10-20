/**
 * The client's own callback endpoint.
 *
 * The sandbox posts payment events here the way it would post to a merchant's
 * server. The suite reads back what arrived over HTTP, so "the webhook was
 * delivered" is proven by a payload the endpoint actually received — not by a
 * dashboard counter.
 */
import { createServer } from "node:http";

const port = Number(process.env.E2E_CALLBACK_PORT ?? 3099);

/** Every body the endpoint has received, oldest first. */
const received = [];

const server = createServer((req, res) => {
  // The suite reads the log back through the same origin, so the two processes
  // do not have to share memory.
  if (req.method === "GET" && req.url === "/__received") {
    res
      .writeHead(200, { "Content-Type": "application/json" })
      .end(JSON.stringify(received));
    return;
  }

  if (req.method !== "POST") {
    res.writeHead(405).end();
    return;
  }

  let raw = "";
  req.on("data", (chunk) => {
    raw += chunk;
  });
  req.on("end", () => {
    let payload = null;
    try {
      payload = JSON.parse(raw);
    } catch {
      payload = raw;
    }
    received.push({ url: req.url, payload, at: Date.now() });
    res.writeHead(200, { "Content-Type": "application/json" }).end(
      JSON.stringify({ ok: true })
    );
  });
});

server.listen(port, "127.0.0.1", () => {
  console.log(`callback endpoint listening on http://127.0.0.1:${port}/callback`);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => {
    server.close(() => process.exit(0));
  });
}
