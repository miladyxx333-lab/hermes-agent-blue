import { execute, testEnvironment } from "./dist/server/index.js";

const config = {
  hermesCommand: "../venv/bin/hermes",
  model: "gemini-2.5-flash",
  provider: "google",
  timeoutSec: 120,
};

async function run() {
  console.log("== Testing Environment ==");
  const testRes = await testEnvironment({ config });
  console.log(testRes);
  if (testRes.status === "fail") {
    console.log("Environment test failed. Exiting.");
    return;
  }

  console.log("\n== Executing Adapter ==");
  const ctx = {
    agent: { adapterConfig: config },
    config: {
      taskId: "test-task",
      taskTitle: "Say Hello",
      taskBody: "Please respond with 'Hello, Paperclip Adapter is working fine in Hermes Agent Blue!' and nothing else."
    },
    runId: "run-" + Date.now(),
    onLog: (type, chunk) => process.stdout.write(`[LOG ${type}] ${chunk}`),
  };

  const execRes = await execute(ctx);
  console.log("\n== Execution Output ==");
  console.log("Summary:", execRes.summary || "(none)");
  console.log("Exit Code:", execRes.exitCode);
  console.log("Timed Out:", execRes.timedOut);
}

run().catch(console.error);
