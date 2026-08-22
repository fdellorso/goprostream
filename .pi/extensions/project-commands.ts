import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execSync } from "node:child_process";
import { writeFileSync, mkdirSync, existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

/**
 * Project Commands Extension
 *
 * Comandi custom per il progetto goprostream:
 * - /handoff — Genera documento di handoff
 * - /commit — Crea un commit git con messaggio strutturato
 * - /status — Verifica stato di tutti i componenti
 * - /stream — Avvia il pipeline di streaming
 */
export default function (pi: ExtensionAPI) {
  const cwd = process.cwd();

  // ─── /handoff ──────────────────────────────────────────────
  pi.registerCommand("handoff", {
    description: "Genera un documento di handoff in docs/handoff/",
    handler: async (args, ctx) => {
      const timestamp = new Date().toISOString().slice(0, 10);
      const time = new Date().toLocaleTimeString("it-IT", {
        hour: "2-digit",
        minute: "2-digit",
      });
      const handoffDir = join(cwd, "docs", "handoff");
      if (!existsSync(handoffDir)) mkdirSync(handoffDir, { recursive: true });

      // Raccogli info
      let gitLog = "";
      let gitDiff = "";
      let branch = "";
      try {
        branch = execSync("git rev-parse --abbrev-ref HEAD", {
          encoding: "utf-8",
        }).trim();
        gitLog = execSync("git log --oneline -10", { encoding: "utf-8" }).trim();
        gitDiff = execSync("git diff --stat", { encoding: "utf-8" }).trim();
      } catch {
        gitLog = "(git non disponibile)";
      }

      // Conta warning pyright
      let pyrightReport = "";
      try {
        pyrightReport = execSync("npx pyright 2>&1 | tail -5", {
          encoding: "utf-8",
          timeout: 30000,
        }).trim();
      } catch (e: any) {
        pyrightReport = e.stdout?.slice(-200) || "(pyright non disponibile)";
      }

      const content = `# Handoff — ${timestamp} ${time}

## Contesto

- **Branch**: ${branch}
- **Comando**: ${args || "(nessuna nota specifica)"}

## Stato Progetto

### Ultimi commit

\`\`\`
${gitLog}
\`\`\`

### Modifiche non committate

\`\`\`
${gitDiff || "(nessuna modifica)"}
\`\`\`

### Type Check (pyright)

\`\`\`
${pyrightReport}
\`\`\`

## Note

${args || "_Nessuna nota specifica fornita._"}

## Prossimi Passi

- [ ] _Da definire_
`;

      const filename = `handoff-${timestamp}-${time.replace(":", "")}.md`;
      const filepath = join(handoffDir, filename);
      writeFileSync(filepath, content);

      ctx.ui.notify(`Handoff salvato: docs/handoff/${filename}`, "info");
    },
  });

  // ─── /commit ──────────────────────────────────────────────
  pi.registerCommand("commit", {
    description: "Crea un git commit con messaggio strutturato",
    handler: async (args, ctx) => {
      if (!args) {
        ctx.ui.notify(
          "Uso: /commit <tipo>: <descrizione>\nTipi: feat, fix, docs, refactor, chore",
          "error"
        );
        return;
      }

      // Valida formato
      const validTypes = ["feat", "fix", "docs", "refactor", "chore", "test", "style"];
      const match = args.match(/^(\w+):\s*(.+)$/);
      if (!match) {
        ctx.ui.notify(
          "Formato: /commit <tipo>: <descrizione>\nEsempio: /commit feat: aggiunta gestione stream HLS",
          "error"
        );
        return;
      }

      const [, type, desc] = match;
      if (!validTypes.includes(type)) {
        ctx.ui.notify(
          `Tipo non valido: "${type}". Tipi ammessi: ${validTypes.join(", ")}`,
          "error"
        );
        return;
      }

      try {
        // Aggiungi tutto e committa
        execSync("git add -A", { cwd });
        execSync(`git commit -m "${type}: ${desc}"`, { cwd, encoding: "utf-8" });
        ctx.ui.notify(`Commit creato: ${type}: ${desc}`, "info");
      } catch (e: any) {
        const output = e.stdout || e.message || "Errore sconosciuto";
        ctx.ui.notify(`Errore commit:\n${output}`, "error");
      }
    },
  });

  // ─── /status ──────────────────────────────────────────────
  pi.registerCommand("status", {
    description: "Verifica stato di tutti i componenti del progetto",
    handler: async (_args, ctx) => {
      const checks: string[] = [];

      // Git
      try {
        const branch = execSync("git rev-parse --abbrev-ref HEAD", {
          encoding: "utf-8",
        }).trim();
        const status = execSync("git status --porcelain", {
          encoding: "utf-8",
        }).trim();
        const modCount = status ? status.split("\n").length : 0;
        checks.push(`Git: branch ${branch}, ${modCount} modifiche`);
      } catch {
        checks.push("Git: non disponibile");
      }

      // Podman
      try {
        const ps = execSync("podman-compose ps --format '{{.Name}}: {{.Status}}'", {
          encoding: "utf-8",
          cwd,
        }).trim();
        checks.push(`Podman: ${ps || "nessun container"}`);
      } catch {
        checks.push("Podman: non disponibile o compose non avviato");
      }

      // FFmpeg
      try {
        const ffmpeg = execSync("pgrep -a ffmpeg || echo 'non attivo'", {
          encoding: "utf-8",
        }).trim();
        checks.push(`FFmpeg: ${ffmpeg.includes("ffmpeg") ? "attivo" : "non attivo"}`);
      } catch {
        checks.push("FFmpeg: non verificabile");
      }

      // GoPro
      try {
        const ping = execSync("timeout 2 ping -c 1 10.5.5.9 2>/dev/null && echo raggiungibile || echo non_raggiungibile", {
          encoding: "utf-8",
        }).trim();
        checks.push(`GoPro: ${ping.includes("raggiungibile") ? "connessa" : "non connessa"}`);
      } catch {
        checks.push("GoPro: non raggiungibile");
      }

      // Pyright
      try {
        const pyright = execSync("npx pyright 2>&1 | tail -1", {
          encoding: "utf-8",
          timeout: 30000,
        }).trim();
        checks.push(`Pyright: ${pyright}`);
      } catch {
        checks.push("Pyright: non disponibile");
      }

      ctx.ui.notify(checks.join("\n"), "info");
    },
  });

  // ─── /stream ──────────────────────────────────────────────
  pi.registerCommand("stream", {
    description: "Avvia il pipeline di streaming (podman-compose + goprostream.py)",
    handler: async (_args, ctx) => {
      try {
        ctx.ui.notify("Avvio nginx-rtmp...", "info");
        execSync("podman-compose up -d", { cwd, encoding: "utf-8" });
        ctx.ui.notify(
          "nginx-rtmp avviato. Ora esegui: pipenv run python goprostream.py",
          "info"
        );
      } catch (e: any) {
        ctx.ui.notify(`Errore avvio podman-compose:\n${e.message}`, "error");
      }
    },
  });
}
