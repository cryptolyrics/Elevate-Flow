import { buildApp } from "./server";
import { getConfigPath, loadConfig } from "./config";
import { OpenClawCliProvider } from "./openclaw-cli-provider";
import { Poller } from "./poller";

async function main(): Promise<void> {
  const configPath = getConfigPath();
  const config = loadConfig(configPath);

  const provider = new OpenClawCliProvider(config.openClawBin);
  const poller = new Poller(config, provider);

  await poller.pollOnce();
  poller.start();

  const app = buildApp(config, poller);
  const server = app.listen(config.port, config.host, () => {
    console.log(`clerk-service listening on http://${config.host}:${config.port}`);
  });

  const shutdown = () => {
    poller.stop();
    server.close(() => process.exit(0));
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

main().catch((err) => {
  console.error("Fatal clerk-service error", err);
  process.exit(1);
});
