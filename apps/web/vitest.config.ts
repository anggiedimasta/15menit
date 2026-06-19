import { readFileSync } from "node:fs";
import tailwindcss from "@tailwindcss/vite";
import viteReact from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const pkg = JSON.parse(
  readFileSync(new URL("./package.json", import.meta.url), "utf8"),
) as { version: string };

export default defineConfig({
  resolve: { tsconfigPaths: true },
  define: {
    __APP_PACKAGE_VERSION__: JSON.stringify(pkg.version),
  },
  plugins: [tailwindcss(), viteReact()],
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
