import { useEffect, useState } from "react";
import { Cloud, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";

type CloudStatus = {
  phase?: string;
  overall_percent?: number;
  current_employee?: string;
  current_task?: string;
  run_number?: string | number;
};

export function CloudProductionBar() {
  const [status, setStatus] = useState<CloudStatus | null>(null);
  const [topic, setTopic] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const refresh = async () => {
    try {
      const response = await fetch("/api/status?ts=" + Date.now(), {
        cache: "no-store",
      });
      if (!response.ok) return;
      setStatus(await response.json());
    } catch {
      // Status polling is best-effort; the production API reports actionable errors.
    }
  };

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 15000);
    return () => window.clearInterval(timer);
  }, []);

  const start = async () => {
    if (busy) return;

    setBusy(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch("/api/run-reels", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: topic.trim(),
          plan_only: false,
        }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.error || "Cloud production could not be started.");
      }

      setMessage(data.message || "Cloud production dispatched.");
      setTopic("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cloud production failed.");
    } finally {
      setBusy(false);
    }
  };

  const pct = Math.max(
    0,
    Math.min(100, Number(status?.overall_percent || 0))
  );
  const phase = status?.phase || "Waiting";
  const hasError = Boolean(error);

  return (
    <div className="mx-auto mb-5 max-w-7xl rounded-2xl border border-indigo-200 bg-white/90 p-4 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <Cloud className="h-4 w-4 text-indigo-600" />
            <span className="text-sm font-semibold text-slate-900">
              24×7 Cloud Production
            </span>
            {status?.run_number ? (
              <span className="text-xs text-slate-500">
                Run #{status.run_number}
              </span>
            ) : null}
            {busy ? (
              <Loader2 className="h-4 w-4 animate-spin text-indigo-600" />
            ) : hasError ? (
              <AlertCircle className="h-4 w-4 text-red-500" />
            ) : pct >= 100 ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            ) : null}
          </div>

          <p className="mt-1 truncate text-xs text-slate-600">
            {status?.current_employee || "AI Manager / CEO"} ·{" "}
            {status?.current_task || phase}
          </p>

          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-indigo-600 transition-all duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            {phase} · {pct}%
          </div>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void start();
            }}
            placeholder="Optional topic, e.g. Ganesh Chaturthi"
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-200"
            disabled={busy}
          />
          <button
            onClick={() => void start()}
            disabled={busy}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy ? "Starting…" : "Run 4 Reels"}
          </button>
        </div>
      </div>

      {message ? (
        <p className="mt-2 text-xs text-emerald-700">{message}</p>
      ) : null}
      {error ? <p className="mt-2 text-xs text-red-600">{error}</p> : null}
    </div>
  );
}
