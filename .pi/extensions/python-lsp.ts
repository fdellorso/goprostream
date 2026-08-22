import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execSync } from "node:child_process";

/**
 * Python LSP Extension
 *
 * Registra un tool custom che esegue pyright per diagnosticare
 * il codice Python del progetto e restituisce i warning/error.
 */
export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "python_typecheck",
    label: "Python Type Check",
    description:
      "Esegue pyright sul progetto Python e restituisce warning ed errori di tipo. Utile dopo modifiche ai file .py.",
    parameters: {
      type: "object",
      properties: {
        file: {
          type: "string",
          description:
            "File Python da verificare (opzionale, se omesso verifica tutto il progetto)",
        },
      },
    },
    async execute(toolCallId: string, params: { file?: string }) {
      try {
        const fileArg = params.file ? ` ${params.file}` : "";
        const output = execSync(`npx pyright${fileArg} 2>&1`, {
          encoding: "utf-8",
          timeout: 30000,
          cwd: process.cwd(),
        });
        return {
          content: [{ type: "text", text: output }],
          details: { tool: "pyright", file: params.file ?? "all" },
        };
      } catch (error: any) {
        // pyright exits with code 1 when there are errors - that's expected
        const output = error.stdout || error.message || "Unknown error";
        return {
          content: [{ type: "text", text: output }],
          details: { tool: "pyright", hasErrors: true },
        };
      }
    },
  });

  pi.registerCommand("typecheck", {
    description: "Esegue pyright sul progetto Python",
    handler: async (args, ctx) => {
      try {
        const fileArg = args ? ` ${args}` : "";
        const output = execSync(`npx pyright${fileArg} 2>&1`, {
          encoding: "utf-8",
          timeout: 30000,
        });
        ctx.ui.notify(output, "info");
      } catch (error: any) {
        ctx.ui.notify(error.stdout || "Type check failed", "error");
      }
    },
  });
}
