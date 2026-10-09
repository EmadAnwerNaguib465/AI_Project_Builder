"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUpRight, Asterisk, Boxes, Check, CircleHelp, FileCheck2, FileText, Layers3, LoaderCircle, Pause, Play, RotateCcw, ScanEye, ScanSearch, ShieldCheck, TrendingUp } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import ReportView from "@/components/report-view";
import { AGENTS, type AgentName, type PipelineEvent, type ProjectReport } from "@/lib/types";

import PipelineMap from "@/components/pipeline-map";
import { Intro, StudioHeader } from "@/components/studio-chrome";
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
  const [exampleIndex, setExampleIndex] = useState(0);
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
    if (event.type === "step") {
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

  const progress = mode === "complete" ? 100 : Math.round(completed.length / AGENTS.length * 100);
  const selectedExample = EXAMPLES.findIndex((example) => example.idea === idea);
  const chooseExample = (index: number) => {
    if (mode === "running") return;
    setIdea(EXAMPLES[index].idea);
    setError("");
    setMode("idle");
    setExampleIndex(index);
    document.getElementById("idea")?.focus({ preventScroll: true });
  };
  const exampleTitles = ["An eye for every detail.", "Knowledge, connected.", "See what comes next."];
  const ExampleIcon = EXAMPLE_ICONS[exampleIndex];
  const reveal = { initial: reduceMotion ? false as const : { opacity: 0, y: 24 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true, amount: 0.12 }, transition: { duration: 0.65 } };

  return <main className="app-shell" data-motion={scenePaused || reduceMotion ? "paused" : "active"} data-mode={mode}>
    <Intro />
    <StudioHeader hasReport={Boolean(report)} />
    <section id="workspace" className="workspace" aria-labelledby="workspace-title">
      <div className="hero-content shell">
        <div className="hero-copy">
          <span className="eyebrow"><i /> THE AI PROJECT STUDIO</span>
          <h1 id="workspace-title"><span>AI Project</span><span>Builder<span className="title-dot">.</span></span></h1>
          <p className="hero-description">Your idea, researched and reviewed.<br />A clear plan for what comes next.</p>
          {mode !== "complete" ? <form className="brief-form" onSubmit={(event) => { event.preventDefault(); void submit(); }}>
            <div className="form-heading"><label htmlFor="idea">Your project idea</label><span>{idea.length} / 2000</span></div>
            <textarea id="idea" value={idea} onChange={(event) => setIdea(event.target.value)} maxLength={2000} disabled={mode === "running"} placeholder="A study assistant that answers questions from course PDFs and cites its sources..." rows={5} />
            <div className="example-list">{EXAMPLES.map((example, index) => { const Icon = EXAMPLE_ICONS[index]; return <button key={example.label} type="button" aria-pressed={selectedExample === index} disabled={mode === "running"} onClick={() => chooseExample(index)}><Icon size={14} />{example.label}</button>; })}</div>
            <div className="form-bottom"><button type="submit" className="build-button pill-button" disabled={mode === "running" || service === "offline"}><span>{mode === "running" ? "Building your plan" : "Build project plan"}</span><span className="button-badge">{mode === "running" ? <LoaderCircle size={18} className="spin" /> : <ArrowUpRight size={20} />}</span></button><a href="#pipeline" className="text-link">The process <ArrowDown size={15} /></a></div>
            {mode === "error" && <div className="inline-error" role="alert"><CircleHelp size={18} /><span>{error}</span><button type="button" onClick={submit}>Retry</button></div>}
          </form> : <div className="complete-brief"><span><Check size={18} />Your blueprint is ready.</span><a className="pill-button" href="#blueprint">View your plan<span className="button-badge"><ArrowDown size={18} /></span></a><button className="text-link" type="button" onClick={reset}><RotateCcw size={16} />New plan</button></div>}
        </div>
        <aside className="hero-side">
          <PipelineMap current={current} completed={completed} complete={mode === "complete"} paused={scenePaused || Boolean(reduceMotion)} />
          <div className="example-carousel">
            <div className="carousel-top"><span className="carousel-symbol"><ExampleIcon size={29} strokeWidth={1.3} /></span><div key={exampleIndex} className="carousel-title"><span>PROJECT DIRECTION / 0{exampleIndex + 1}</span><strong>{exampleTitles[exampleIndex]}</strong></div></div>
            <div className="carousel-bottom"><button type="button" className="text-link" disabled={mode === "running"} onClick={() => chooseExample(exampleIndex)}>Use this idea <ArrowUpRight size={13} /></button><div className="carousel-controls"><button type="button" aria-label="Previous idea" title="Previous idea" onClick={() => setExampleIndex((exampleIndex + 2) % 3)}><ArrowLeft size={14} /></button><button type="button" aria-label="Next idea" title="Next idea" onClick={() => setExampleIndex((exampleIndex + 1) % 3)}><ArrowRight size={14} /></button></div></div>
          </div>
          <div className="hero-readout"><span>YOUR BUILD TEAM</span><div>{AGENTS.map((agent, index) => <span key={agent.id} className={completed.includes(agent.id) || mode === "complete" ? "done" : current === agent.id ? "active" : ""}><i />{String(index + 1).padStart(2, "0")} {agent.label}</span>)}</div></div>
        </aside>
      </div>
      <div className="hero-status shell"><span className={`service-indicator ${service}`}><i />{service === "checking" ? "Connecting" : service === "ready" ? "System ready" : "Service offline"}</span><span className="hero-status-middle">{mode === "running" ? `${AGENTS.find((agent) => agent.id === current)?.label ?? "Planning"} in progress` : "FROM A THOUGHT. TO A PLAN."}</span><button className="scene-toggle" type="button" disabled={Boolean(reduceMotion)} title={reduceMotion ? "Reduced motion is enabled" : scenePaused ? "Play visual effects" : "Pause visual effects"} aria-label={scenePaused ? "Play visual effects" : "Pause visual effects"} aria-pressed={scenePaused || Boolean(reduceMotion)} onClick={() => setScenePaused((value) => !value)}>{scenePaused || reduceMotion ? <Play size={14} /> : <Pause size={14} />}</button></div>
    </section>

    <section className="studio-statement shell" aria-label="Project planning">
      <span className="eyebrow"><i /> IDEA TO IMPLEMENTATION</span>
      <motion.h2 {...reveal}>A little ambition.<br /><span>A well-considered next step.</span></motion.h2>
      <div className="create-band" aria-hidden="true"><span>You</span><span>Imagine</span><span><ArrowRight size={44} /></span><span>We plan.</span></div>
    </section>

    <section id="ideas" className="ideas-section shell" aria-labelledby="ideas-title">
      <div className="section-head"><div><span className="eyebrow"><i /> A STARTING POINT</span><h2 id="ideas-title">Ideas worth building.</h2></div><span className="section-aside">03 PROJECT DIRECTIONS</span></div>
      <div className="idea-grid">{EXAMPLES.map((example, index) => { const Icon = EXAMPLE_ICONS[index]; return <motion.button {...reveal} transition={{ duration: 0.6, delay: index * 0.08 }} type="button" className={`idea-card idea-card-${index}`} key={example.label} disabled={mode === "running"} onClick={() => { chooseExample(index); document.getElementById("workspace")?.scrollIntoView({ behavior: "instant" }); }}><span key="meta" className="idea-card-meta"><span>0{index + 1} / {example.label}</span><span className="round-arrow"><ArrowUpRight size={19} /></span></span><span key="art" className="idea-art" aria-hidden="true"><Icon size={84} strokeWidth={0.8} /><i /><i /></span><span key="copy" className="idea-card-copy"><strong>{exampleTitles[index]}</strong><span>{index === 0 ? "Visual inspection. Defect detection. Quality, at scale." : index === 1 ? "Your documents. Grounded answers. Sources included." : "Customer signals. Clear predictions. Informed decisions."}</span><span className="idea-tag">{index === 0 ? "Computer vision" : index === 1 ? "Retrieval-augmented generation" : "Predictive machine learning"}</span></span></motion.button>; })}</div>
    </section>

    <section id="pipeline" className="pipeline-section shell" aria-labelledby="pipeline-title">
      <div className="section-head"><div><span className="eyebrow"><i /> THE PROCESS</span><h2 id="pipeline-title">Six perspectives.<br />One considered plan.</h2></div><div className="process-status" aria-live="polite"><span>{mode === "running" ? "In progress" : mode === "complete" ? "Complete" : mode === "error" ? "On hold" : "Standing by"}</span><strong className="process-percent">{String(progress).padStart(2, "0")}<small>%</small></strong></div></div>
      <div className="progress-track" role="progressbar" aria-label="Project plan progress" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}><span style={{ width: `${progress}%` }} /></div>
      <div className="agent-grid">{AGENTS.map((agent, index) => { const done = completed.includes(agent.id) || mode === "complete"; const active = mode === "running" && current === agent.id; const Icon = AGENT_ICONS[index]; return <motion.div {...reveal} key={agent.id} className={`agent-item ${done ? "done" : ""} ${active ? "active" : ""}`}><span key="number" className="agent-number">0{index + 1}</span><div key="icon" className="agent-icon">{done ? <Check size={23} /> : <Icon size={23} strokeWidth={1.4} />}</div><strong key="label">{agent.label}</strong><span key="detail" className="agent-detail">{agent.detail}</span><span key="state" className="agent-state">{active && <LoaderCircle size={13} className="spin" />}{done ? "COMPLETE" : active ? "WORKING" : "QUEUED"}</span><ArrowUpRight key="arrow" className="agent-arrow" size={21} /></motion.div>; })}</div>
      {revisions > 0 && <p className="revision-note"><RotateCcw size={13} />Review cycle {revisions} {mode === "complete" ? "completed." : "in progress."}</p>}
    </section>

    <AnimatePresence>{report && mode === "complete" && <motion.div id="blueprint" ref={resultRef} className="report-transition" initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><ReportView report={report} onReset={reset} /></motion.div>}</AnimatePresence>
    <footer className="footer"><div className="shell"><div className="footer-cta"><h2>Your next big idea.<br /><span>Starts right here.</span></h2><a className="pill-button light" href="#workspace">Back to your workspace<span className="button-badge"><ArrowUpRight size={21} /></span></a></div><div className="footer-links"><a className="brand" href="#workspace"><Asterisk size={28} />AI Project Builder.</a><nav aria-label="Footer navigation"><a href="#ideas">Project ideas</a><a href="#pipeline">The process</a>{report && <a href="#blueprint">Your blueprint</a>}</nav><span>RESEARCH. ARCHITECTURE. DIRECTION.</span></div><div className="footer-wordmark" aria-hidden="true">BUILDER.</div></div></footer>
  </main>;
}
