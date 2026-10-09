"use client";

import { useEffect, useRef } from "react";
import { ArrowDown, ArrowRight, Boxes, Check, FileCheck2, FileText, Layers3, ScanSearch, ShieldCheck } from "lucide-react";
import { AGENTS, type AgentName } from "@/lib/types";

const ICONS = [FileText, ScanSearch, Layers3, Boxes, ShieldCheck, FileCheck2];

export default function PipelineMap({ current, completed, complete, paused }: {
  current: AgentName | null; completed: AgentName[]; complete: boolean; paused: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    let visible = false;
    let scrolling = false;
    let timer: ReturnType<typeof setTimeout>;
    const preference = matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => { element.dataset.rendering = visible && !scrolling && !document.hidden && !paused && !preference.matches ? "active" : "paused"; };
    const observer = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; sync(); });
    observer.observe(element);
    const onScroll = () => { scrolling = true; sync(); clearTimeout(timer); timer = setTimeout(() => { scrolling = false; sync(); }, 160); };
    window.addEventListener("scroll", onScroll, { passive: true });
    document.addEventListener("visibilitychange", sync);
    preference.addEventListener("change", sync);
    return () => { observer.disconnect(); clearTimeout(timer); window.removeEventListener("scroll", onScroll); document.removeEventListener("visibilitychange", sync); preference.removeEventListener("change", sync); };
  }, [paused]);

  return <div ref={ref} className="pipeline-map" data-rendering="paused" aria-label="Live project workflow">
    <div className="map-heading"><span className="eyebrow"><i /> FROM BRIEF TO BLUEPRINT</span><span>{String(complete ? 6 : completed.length).padStart(2, "0")} / 06</span></div>
    <ol className="flow-grid">{AGENTS.map((agent, index) => {
      const done = complete || completed.includes(agent.id);
      const active = current === agent.id;
      const Icon = ICONS[index];
      return <li key={agent.id} className={`flow-node flow-node-${index} ${done ? "done" : active ? "active" : ""}`}>
        <span className="flow-top"><span className="flow-icon">{done ? <Check size={23} /> : <Icon size={23} strokeWidth={1.4} />}</span><span>0{index + 1}</span></span>
        <strong>{agent.label}</strong><span className="flow-detail">{agent.detail}</span>
        <span className="flow-state"><i />{done ? "Complete" : active ? "Working" : "Waiting"}</span>
        {index < 5 && <span className="flow-connector" aria-hidden="true">{index === 2 ? <ArrowDown size={14} /> : <ArrowRight size={14} />}</span>}
      </li>;
    })}</ol>
    <div className="map-output"><FileCheck2 size={17} /><span>{complete ? "Your project blueprint is ready" : "Project blueprint"}</span><span>{complete ? "READY" : "OUTPUT"}</span></div>
  </div>;
}
