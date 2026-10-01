import {useState,useEffect} from "react";
import {ProductionDashboard} from "@/components/ProductionDashboard";
import {ProductionPipeline} from "@/components/ProductionPipeline";
import {ApprovalScreen} from "@/components/ApprovalScreen";
import {productionService} from "@/lib/production-service";
import {ProductionRun} from "@/types/production";
import {CloudProductionBar} from "@/components/CloudProductionBar";
export default function App(){
 const [runs,setRuns]=useState<ProductionRun[]>([]),[selectedRun,setSelectedRun]=useState<ProductionRun|null>(null),[view,setView]=useState<"dashboard"|"pipeline"|"approval">("dashboard");
 useEffect(()=>{setRuns(productionService.getRuns());return productionService.subscribe(r=>setRuns(prev=>prev.map(x=>x.id===r.id?r:x).some(x=>x.id===r.id)?prev.map(x=>x.id===r.id?r:x):[r,...prev]))},[]);
 const handleNewRun=(topic:string,festivalId:string,language:string)=>{const run=productionService.createRun(topic,festivalId,language);setRuns(productionService.getRuns());setSelectedRun(run);setView("pipeline")};
 const handleRunUpdate=(r:ProductionRun)=>{setRuns(productionService.getRuns());setSelectedRun(r)};
 const handleApprove=(id:string)=>{const r=productionService.approveRun(id);if(r){handleRunUpdate(r);setView("dashboard")}};
 const handleReject=(id:string,reason:string)=>{const r=productionService.rejectRun(id,reason);if(r){handleRunUpdate(r);setView("pipeline")}};
 return <div className="min-h-screen bg-gradient-to-b from-slate-50 via-indigo-50/50 to-slate-50"><div className="px-4 pt-4"><CloudProductionBar/></div>
 {view==="dashboard"&&<ProductionDashboard runs={runs} onNewRun={handleNewRun} onSelectRun={r=>{setSelectedRun(r);setView(r.status==="NEEDS_REVIEW"?"approval":"pipeline")}}/>}
 {view==="pipeline"&&selectedRun&&<ProductionPipeline run={selectedRun} onUpdate={handleRunUpdate} onBack={()=>setView("dashboard")} onReview={()=>setView("approval")}/>}
 {view==="approval"&&selectedRun&&<ApprovalScreen run={selectedRun} onApprove={handleApprove} onReject={handleReject} onBack={()=>setView("pipeline")}/>}
 </div>
}