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
 * - /debug — Diagnostica completa del sistema
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
        // Aggiungi solo file tracked modificati (no -A)
        execSync("git add -u", { cwd });
        // Verifica se ci sono staged changes
        const staged = execSync("git diff --cached --name-only", {
          cwd,
          encoding: "utf-8",
        }).trim();
        if (!staged) {
          ctx.ui.notify("Nessuna modifica da committare", "error");
          return;
        }
        execSync(`git commit -m "${type}: ${desc}"`, { cwd, encoding: "utf-8" });
        const fileList = staged.split("\n").join(", ");
        ctx.ui.notify(`Commit creato: ${type}: ${desc}\nFile: ${fileList}`, "info");
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

      // GoPro (usa curl, NON ping — vedi AGENTS.md)
      try {
        const status = execSync("curl -s --max-time 3 http://10.5.5.9/gp/gpControl/status", {
          encoding: "utf-8",
        }).trim();
        const parsed = JSON.parse(status);
        const goproStatus = parsed.status?.["3"] ?? "unknown";
        checks.push(`GoPro: connessa (status: ${goproStatus})`);
      } catch {
        checks.push("GoPro: non connessa o non raggiungibile");
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
    description: "Avvia lo stack di streaming (podman-compose up -d)",
    handler: async (_args, ctx) => {
      try {
        ctx.ui.notify("Avvio stack streaming...", "info");
        execSync("podman-compose up -d", { cwd, encoding: "utf-8" });
        ctx.ui.notify("Stack avviato. Container: nginx-rtmp + goprostream", "info");
      } catch (e: any) {
        ctx.ui.notify(`Errore avvio stack:\n${e.message}`, "error");
      }
    },
  });

  // ─── /debug ──────────────────────────────────────────────
  pi.registerCommand("debug", {
    description: "Diagnostica completa: GoPro, FFmpeg, Nginx, HLS, Python",
    handler: async (_args, ctx) => {
      const results: string[] = [];
      const ok = "\u2705";
      const fail = "\u274c";
      const warn = "\u26a0\ufe0f";

      // 1. GoPro
      try {
        const status = execSync("curl -s --max-time 3 http://10.5.5.9/gp/gpControl/status", {
          encoding: "utf-8",
        }).trim();
        const parsed = JSON.parse(status);
        const wifi = parsed.status?.["3"] ?? "?";
        const recording = parsed.status?.["50"] ?? "?";
        results.push(`${ok} GoPro: WiFi=${wifi}, REC=${recording}`);
      } catch {
        results.push(`${fail} GoPro: non raggiungibile`);
      }

      // 2. FFmpeg
      try {
        const ffmpeg = execSync('pgrep -a ffmpeg 2>/dev/null || echo ""', {
          encoding: "utf-8",
        }).trim();
        if (ffmpeg) {
          const pid = ffmpeg.split(" ")[0];
          results.push(`${ok} FFmpeg: attivo (PID ${pid})`);
        } else {
          results.push(`${warn} FFmpeg: non attivo`);
        }
      } catch {
        results.push(`${fail} FFmpeg: non verificabile`);
      }

      // 3. Container Podman
      try {
        const ps = execSync(
          "podman-compose -f docker/docker-compose.yml ps --format '{{.Name}}: {{.Status}}'",
          { encoding: "utf-8", cwd }
        ).trim();
        if (ps) {
          ps.split("\n").forEach((line) => {
            const up = line.includes("Up");
            results.push(`${up ? ok : fail} Container: ${line}`);
          });
        } else {
          results.push(`${warn} Container: nessuno in esecuzione`);
        }
      } catch {
        results.push(`${fail} Podman: compose non disponibile`);
      }

      // 4. Nginx RTMP stat
      try {
        const stat = execSync("curl -s --max-time 3 http://localhost:8080/stat", {
          encoding: "utf-8",
        });
        const hasLive = stat.includes("<live>");
        const hasStream = stat.includes("gopro");
        if (hasStream) {
          results.push(`${ok} RTMP: stream gopro attivo`);
        } else if (hasLive) {
          results.push(`${warn} RTMP: nginx attivo, nessuno stream attivo`);
        } else {
          results.push(`${fail} RTMP: stat non raggiungibile`);
        }
      } catch {
        results.push(`${fail} RTMP: nginx non raggiungibile`);
      }

      // 5. HLS endpoint
      try {
        const hls = execSync(
          "curl -s -o /dev/null -w '%{http_code}' --max-time 3 http://localhost:8080/hls/gopro.m3u8",
          { encoding: "utf-8" }
        ).trim();
        if (hls === "200") {
          results.push(`${ok} HLS: /hls/gopro.m3u8 disponibile`);
        } else {
          results.push(`${warn} HLS: stato HTTP ${hls}`);
        }
      } catch {
        results.push(`${fail} HLS: endpoint non raggiungibile`);
      }

      // 6. Pyright
      try {
        const pyright = execSync("npx pyright 2>&1 | tail -3", {
          encoding: "utf-8",
          timeout: 30000,
        }).trim();
        const errors = pyright.match(/(\d+) error/)?.[1] ?? "?";
        const warnings = pyright.match(/(\d+) warning/)?.[1] ?? "?";
        const clean = errors === "0" && warnings === "0";
        results.push(`${clean ? ok : warn} Pyright: ${errors} errori, ${warnings} warning`);
      } catch {
        results.push(`${fail} Pyright: non disponibile`);
      }

      ctx.ui.notify(
        `=== DIAGNOSTICA ===\n${results.join("\n")}`,
        "info"
      );
    },
  });
}
