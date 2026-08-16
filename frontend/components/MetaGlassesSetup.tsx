"use client";

import { useState } from "react";

type ConnectionState = "idle" | "checking" | "ready" | "locked" | "offline";

export default function MetaGlassesSetup() {
  const [backend, setBackend] = useState("http://127.0.0.1:8420");
  const [state, setState] = useState<ConnectionState>("idle");

  async function checkConnection() {
    setState("checking");
    try {
      const base = backend.trim().replace(/\/$/, "");
      const response = await fetch(`${base}/api/wearables/v1/capabilities`, {
        signal: AbortSignal.timeout(2500),
      });
      if (!response.ok) {
        setState("offline");
        return;
      }
      const capabilities = (await response.json()) as { ready?: boolean };
      setState(capabilities.ready ? "ready" : "locked");
    } catch {
      setState("offline");
    }
  }

  return (
    <div className="mx-auto mt-rest max-w-[48rem] rounded-card border border-hairline bg-paper p-6 text-left sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="font-mono text-label uppercase text-offset-ink">
            Native companion required
          </p>
          <h3 className="mt-2 font-display text-title">Wear the camera. Keep the brain here.</h3>
          <p className="mt-2 max-w-[58ch] text-caption text-graphite">
            The browser does not connect to the glasses directly. Meta&apos;s Device Access
            Toolkit runs in an Android companion, which sends fresh frames into the same
            Slopify pipeline as every video below.
          </p>
        </div>
        <span className="rounded-full border border-offset-ink/25 px-3 py-1 font-mono text-label uppercase text-offset-ink">
          Meta DAT 0.9
        </span>
      </div>

      <ol className="mt-6 grid gap-3 text-caption text-ink sm:grid-cols-3">
        <li className="border-t border-hairline pt-3">
          <span className="font-mono text-label text-graphite">01</span>
          <span className="mt-1 block">Run Slopify on the same Wi-Fi with LAN mode.</span>
        </li>
        <li className="border-t border-hairline pt-3">
          <span className="font-mono text-label text-graphite">02</span>
          <span className="mt-1 block">Register the companion through Meta AI.</span>
        </li>
        <li className="border-t border-hairline pt-3">
          <span className="font-mono text-label text-graphite">03</span>
          <span className="mt-1 block">Start the camera session and live bridge.</span>
        </li>
      </ol>

      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <label className="min-w-0 flex-1">
          <span className="sr-only">Slopify backend address</span>
          <input
            value={backend}
            onChange={(event) => {
              setBackend(event.target.value);
              setState("idle");
            }}
            inputMode="url"
            spellCheck={false}
            className="w-full rounded-full border border-ink/20 bg-bone px-5 py-3 font-mono text-label text-ink outline-none transition focus:border-ink/60"
          />
        </label>
        <button
          type="button"
          onClick={() => void checkConnection()}
          disabled={state === "checking"}
          className="rounded-full border border-ink/25 px-6 py-3 font-mono text-label uppercase transition hover:border-ink/60 disabled:cursor-wait disabled:text-graphite"
        >
          {state === "checking" ? "Checking…" : "Check connection"}
        </button>
      </div>

      <p aria-live="polite" className="mt-3 min-h-5 font-mono text-label uppercase text-graphite">
        {state === "ready" && "Wearables API v1 is ready"}
        {state === "locked" && "Backend found · set the LAN wearable token"}
        {state === "offline" && "Not reachable · use the local site or verify with curl"}
        {state === "idle" && "Connection check only — the companion starts the stream"}
      </p>
    </div>
  );
}
