import { defineConfig } from "vitest/config";

// Components need a browser-like environment; plain library tests do not.
export default defineConfig({ test: { environment: "jsdom" } });
