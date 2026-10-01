import { useEffect, useState } from "react";

type CloudStatus = { phase?: string; overall_percent?: number; current_employee?: string; current_task?: string; run_number?: string | number; };

export function CloudProductionBar() {
  const [status, setStatus] = useState<CloudStatus | null>(null);
  const [topic, setTopic] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const refresh = async () => { try { const r=await fetch("/api/status?ts="+Date.now(),{cache:"no-store"}); if(r.ok)setStatus(await r.json()); } catch {} };
  useEffect(()=>{refresh();const id=window.setInterval(refresh,15000);return()=>window.clearInterval(id)},[]);
  const start=async()=>{setBusy(true);setMessage("");try{const r=await fetch("/api/run-reels",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({topic:topic.trim(),plan_only:false})});const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(data.error||"Cloud production could not be started.");setMessage(data.message||"Cloud production dispatched.");setTopic("");refresh();}catch(e){setMessage(e instanceof Error?e.message:"Cloud production failed.");}finally{setBusy(false);}};
  const pct=Math.max(0,Math.min(100,Number(status?.overall_percent||0)));
  return <div className="mx-auto mb-5 max-w-7xl rounded-2xl border border-indigo-200 bg-white/90 p-4 shadow-sm"><div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div className="min-w-0"><div className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-emerald-500"/><span className="text-sm font-semibold text-slate-900">24×7 Cloud Production</span>{status?.run_number?<span className="text-xs text-slate-500">Run #{status.run_number}</span>:null}</div><p className="mt-1 truncate text-xs text-slate-600">{status?.current_employee||"AI Manager / CEO"} · {status?.current_task||"Waiting for production"}</p><div className="mt-2 h-1.5 w-full max-w-xl overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-indigo-600 transition-all" style={{width:\`\${pct}%\`}}/></div></div><div className="flex flex-col gap-2 sm:flex-row"><input value={topic} onChange={e=>setTopic(e.target.value)} placeholder="Optional topic, e.g. Ganesh Chaturthi" className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-200"/><button onClick={start} disabled={busy} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">{busy?"Starting…":"Run 4 Reels"}</button></div></div>{message?<p className="mt-2 text-xs text-slate-600">{message}</p>:null}</div>;
}