"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { ArrowDown, ArrowRight, ArrowUp, ArrowUpRight, Boxes, Check, CircleHelp, FileCheck2, FileText, Layers3, LoaderCircle, Pause, Play, RotateCcw, ScanEye, ScanSearch, ShieldCheck, Sparkles, TrendingUp } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import ReportView from "@/components/report-view";
import { AGENTS, type AgentName, type PipelineEvent, type ProjectReport } from "@/lib/types";

const PipelineScene = dynamic(() => import("@/components/pipeline-scene"), { ssr: false });
const EXAMPLES = [
  { label: "Vision", idea: "Build a computer vision system that detects product defects on a manufacturing line, using public image datasets and a real-time dashboard." },
  { label: "Knowledge", idea: "Create a RAG assistant that answers student questions from university PDF documents, cites sources, and works with a limited budget." },
  { label: "Prediction", idea: "Design a customer churn prediction system for a subscription business, using tabular data and an interpretable model." },
];
type Mode = "idle" | "running" | "complete" | "error";
const AGENT_ICONS = [FileText, ScanSearch, Layers3, Boxes, ShieldCheck, FileCheck2];
const EXAMPLE_ICONS = [ScanEye, Layers3, TrendingUp];

function parseError(text: string): string {
  try { return JSON.parse(text).detail ?? text; } catch { return text; }
}

export default function StudioPage() {
  const [idea, setIdea] = useState("");
  const [mode, setMode] = useState<Mode>("idle");
  const [completed, setCompleted] = useState<AgentName[]>([]);
  const [current, setCurrent] = useState<AgentName | null>(null);
  const [report, setReport] = useState<ProjectReport | null>(null);
  const [error, setError] = useState("");
  const [revisions, setRevisions] = useState(0);
  const [scenePaused, setScenePaused] = useState(false);
  const [service, setService] = useState<"checking" | "ready" | "offline">("checking");
  const controllerRef = useRef<AbortController | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    fetch("/api/health").then((response) => response.json()).then((health) => setService(health.ok && health.configured ? "ready" : "offline")).catch(() => setService("offline"));
    return () => controllerRef.current?.abort();
  }, []);

  useEffect(() => {
    if (mode !== "complete") return;
    const frame = requestAnimationFrame(() => resultRef.current?.scrollIntoView({ behavior: reduceMotion ? "instant" : "smooth", block: "start" }));
    return () => cancelAnimationFrame(frame);
  }, [mode, reduceMotion]);

  const reset = () => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setMode("idle");
    setIdea("");
    setCompleted([]);
    setCurrent(null);
    setReport(null);
    setError("");
    setRevisions(0);
    window.scrollTo({ top: 0, behavior: reduceMotion ? "instant" : "smooth" });
  };

  const handleEvent = (event: PipelineEvent) => {
    if (event.type === "started") {
      setCurrent("supervisor");
    } else if (event.type === "step") {
      setCompleted((previous) => previous.includes(event.node) ? previous : [...previous, event.node]);
      if (event.revision_count !== null) setRevisions(event.revision_count);
      const next = event.next_agent as AgentName | null;
      if (event.critic_status === "REVISE") {
        setCompleted((previous) => previous.filter((node) => node !== next && node !== "critic"));
      }
      setCurrent(next && AGENTS.some((agent) => agent.id === next) ? next : null);
    } else if (event.type === "complete") {
      setReport(event.report);
      setMode("complete");
      setCurrent(null);
    } else if (event.type === "error") {
      setError(event.message);
      setMode("error");
      setCurrent(null);
    }
  };

  const submit = async () => {
    const clean = idea.trim();
    if (clean.length < 20 || clean.split(/\s+/).length < 5) {
      setError("Describe your idea in at least five words and 20 characters.");
      setMode("error");
      return;
    }
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setMode("running");
    setError("");
    setReport(null);
    setCompleted([]);
    setCurrent("supervisor");
    setRevisions(0);

    try {
      const response = await fetch("/api/build", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea: clean }),
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(parseError(await response.text()));
      if (!response.body) throw new Error("The server returned an empty response.");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finished = false;
      const consume = (line: string) => {
        if (!line.trim()) return;
        const event = JSON.parse(line) as PipelineEvent;
        handleEvent(event);
        if (event.type === "complete" || event.type === "error") finished = true;
      };
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        lines.forEach(consume);
      }
      consume(buffer + decoder.decode());
      if (!finished) throw new Error("The connection ended before the plan was ready.");
    } catch (cause) {
      if (controller.signal.aborted) return;
      setError(cause instanceof Error ? cause.message : "The plan could not be generated.");
      setMode("error");
      setCurrent(null);
    } finally {
      if (controllerRef.current === controller) controllerRef.current = null;
    }
  };

  const activeIndex = mode === "complete" ? 5 : current ? AGENTS.findIndex((agent) => agent.id === current) : -1;
  const progress = mode === "complete" ? 100 : Math.round(completed.length / AGENTS.length * 100);
  const selectedExample = EXAMPLES.findIndex((example) => example.idea === idea);

  return <main className="app-shell" data-motion={scenePaused || reduceMotion ? "paused" : "active"} data-mode={mode}>
    <header className="topbar">
      <a className="brand" href="#workspace" aria-label="Planorai workspace"><Image src="/logo-transparent.png" alt="Planorai" width={140} height={38} priority className="brand-logo" style={{ width: "auto", height: "38px" }} /></a>
      <nav className="top-nav" aria-label="Workspace navigation"><a href="#workspace">Workspace <ArrowUpRight size={13} /></a><a href="#pipeline">Pipeline</a>{report && <a href="#blueprint">Blueprint</a>}</nav>
      <div className="top-actions"><span className={`service-indicator ${service}`}><i />{service === "checking" ? "Connecting" : service === "ready" ? "System ready" : "Service offline"}</span>{mode === "complete" && <button type="button" className="new-plan" title="New plan" aria-label="New plan" onClick={reset}><RotateCcw size={17} /></button>}</div>
    </header>

    <section id="workspace" className={`workspace ${mode === "complete" ? "workspace-compact" : ""}`} aria-labelledby="workspace-title">
      <div className="workspace-guides" aria-hidden="true"><i /><i /><i /><i /></div>
      <div className="workspace-content">
        <div className="workspace-meta"><span className="eyebrow"><span className="live-line" /> PLANORAI STUDIO / 001</span><button className="scene-toggle" type="button" disabled={Boolean(reduceMotion)} title={reduceMotion ? "Reduced motion is enabled" : scenePaused ? "Play 3D animation" : "Pause 3D animation"} aria-label={scenePaused ? "Play 3D animation" : "Pause 3D animation"} aria-pressed={scenePaused || Boolean(reduceMotion)} onClick={() => setScenePaused((value) => !value)}>{scenePaused || reduceMotion ? <Play size={15} /> : <Pause size={15} />}</button></div>
        <div className="workspace-copy">
          <motion.h1 id="workspace-title" initial={reduceMotion ? false : { opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.65 }}><span>AI PROJECT PLANNER</span><span className="title-finish">PLANORAI<span className="title-period">.</span></span></motion.h1>
          <motion.p initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>What will you build next?</motion.p>
        </div>
        <div className="engine-stage">
          <PipelineScene paused={scenePaused || Boolean(reduceMotion)} />
          <aside className="engine-readout" aria-label="Current stage">
            <span className="eyebrow">CURRENT STAGE</span>
            <strong>{mode === "complete" ? "Plan complete" : current ? AGENTS.find((agent) => agent.id === current)?.label : mode === "error" ? "On hold" : "Awaiting brief"}</strong>
            <div className="signal-bars" aria-hidden="true">{Array.from({ length: 18 }, (_, index) => <i key={index} style={{ animationDelay: `${index * -0.13}s`, height: `${8 + ((index * 7) % 23)}px` }} />)}</div>
            <span className="engine-counter"><b>{String(mode === "complete" ? 6 : completed.length).padStart(2, "0")}</b> / 06 COMPLETE</span>
          </aside>
          <div className="engine-caption"><span className="live-line" />{mode === "running" ? "PROCESSING" : mode === "complete" ? "BLUEPRINT READY" : mode === "error" ? "AWAITING RETRY" : "AWAITING YOUR IDEA"}</div>
          <aside className="engine-roster" aria-label="Agent activity">{AGENTS.map((agent, index) => <div key={agent.id} className={`${current === agent.id ? "active" : ""} ${mode === "complete" || completed.includes(agent.id) ? "done" : ""}`}><span>{String(index + 1).padStart(2, "0")}</span><span>{agent.label}</span><i /></div>)}</aside>
        </div>
        {mode !== "complete" && <motion.form className={`brief-form ${mode === "running" ? "is-running" : ""}`} initial={reduceMotion ? false : { opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.15 }} onSubmit={(event) => { event.preventDefault(); void submit(); }}>
          <div className="form-heading"><label htmlFor="idea"><span>01</span> YOUR PROJECT BRIEF</label><span>{String(idea.length).padStart(3, "0")} / 2000</span></div>
          <textarea id="idea" value={idea} onChange={(event) => setIdea(event.target.value)} maxLength={2000} disabled={mode === "running"} placeholder="What do you want to build?" spellCheck="true" />
          <div className="form-bottom"><div className="example-list">{EXAMPLES.map((example, index) => { const Icon = EXAMPLE_ICONS[index]; return <button key={example.label} type="button" aria-pressed={selectedExample === index} disabled={mode === "running"} onClick={() => { setIdea(example.idea); setError(""); setMode("idle"); }}><Icon size={14} />{example.label}<ArrowUpRight size={12} className="example-arrow" /></button>; })}</div><button type="submit" className="build-button" disabled={mode === "running" || service === "offline"}>{mode === "running" ? <><span>Building your plan</span><LoaderCircle size={21} className="spin" /></> : <><span>Build project plan</span><ArrowUpRight size={24} /></>}</button></div>
          {mode === "error" && <div className="inline-error" role="alert"><CircleHelp size={18} /><span>{error}</span><button type="button" onClick={submit}>Retry</button></div>}
        </motion.form>}
        {mode === "complete" && <a className="compact-message" href="#blueprint"><Check size={20} /><span>Your blueprint is ready.</span><ArrowDown size={20} /></a>}
        <div className="workspace-bottom"><span><Sparkles size={13} />{mode === "running" ? "IDEA IN PROGRESS" : mode === "complete" ? "IDEA, MEET BLUEPRINT" : "A LITTLE AMBITION GOES A LONG WAY"}</span><a href="#pipeline">THE PIPELINE <ArrowDown size={14} /></a></div>
      </div>
    </section>

    <section id="pipeline" className="pipeline-section" aria-labelledby="pipeline-title">
      <div className="pipeline-inner">
        <div className="section-head"><div><span className="eyebrow">02 / THE PROCESS</span><h2 id="pipeline-title">The pipeline<span>.</span></h2></div><div className="process-status" aria-live="polite"><span>{mode === "running" ? "In progress" : mode === "complete" ? "Complete" : mode === "error" ? "Paused" : "Standing by"}</span><strong className="process-percent">{String(progress).padStart(2, "0")}<small>%</small></strong></div></div>
        <div className="progress-track" role="progressbar" aria-label="Project plan progress" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}><span style={{ width: `${progress}%` }} /></div>
        <div className="agent-grid">{AGENTS.map((agent, index) => { const done = completed.includes(agent.id) || mode === "complete"; const active = mode === "running" && current === agent.id; const Icon = AGENT_ICONS[index]; return <motion.div key={agent.id} className={`agent-item ${done ? "done" : ""} ${active ? "active" : ""}`} initial={reduceMotion ? false : { opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.2 }} transition={{ duration: 0.3, delay: index * 0.05 }}><div className="agent-topline"><span>{String(index + 1).padStart(2, "0")}</span><ArrowRight size={15} /></div><div className="agent-icon">{done ? <Check size={27} /> : <Icon size={27} strokeWidth={1.5} />}</div><strong>{agent.label}</strong><span className="agent-detail">{agent.detail}</span><span className="agent-state">{active && <LoaderCircle size={11} className="spin" />}{done ? "DONE" : active ? "WORKING" : "QUEUED"}</span></motion.div>; })}</div>
        {revisions > 0 && <p className="revision-note"><RotateCcw size={12} /> Review cycle {revisions} {mode === "complete" ? "completed." : "in progress."}</p>}
      </div>
    </section>

    <AnimatePresence>{report && mode === "complete" && <motion.div id="blueprint" ref={resultRef} className="report-transition" initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.5 }}><ReportView report={report} onReset={reset} /></motion.div>}</AnimatePresence>
    <footer className="footer"><div className="footer-brand"><Image src="/logo-white.png" alt="Planorai" width={130} height={35} className="footer-logo" style={{ width: "auto", height: "32px" }} /></div><span className="footer-note">FROM A THOUGHT. TO A PLAN.</span><a className="back-to-top" href="#workspace" title="Back to workspace" aria-label="Back to workspace"><ArrowUp size={20} /></a></footer>
  </main>;
}
