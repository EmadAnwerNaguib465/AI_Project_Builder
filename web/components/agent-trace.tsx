"use client";

import { useMemo, useState } from "react";
import { ArrowRight, Braces, Check, Copy, ExternalLink, Radio, Route } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { AGENTS, type AgentName, type AgentTraceStep, type TraceSession } from "@/lib/types";

type TraceMode = "idle" | "running" | "complete" | "error";

const agentLabel = (agent: AgentName | null) =>
  AGENTS.find((item) => item.id === agent)?.label ?? "Complete";

function TracePayload({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: Record<string, unknown>;
  accent?: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const json = useMemo(
    () => JSON.stringify(Object.keys(value).length ? value : { status: "No payload" }, null, 2),
    [value],
  );

  const copy = async () => {
    await navigator.clipboard.writeText(json);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  };

  return <section className={`trace-payload ${accent ? "accent" : ""}`}>
    <header>
      <span><Braces size={13} />{label}</span>
      <button type="button" onClick={copy} title={`Copy ${label.toLowerCase()}`} aria-label={`Copy ${label.toLowerCase()}`}>
        {copied ? <Check size={14} /> : <Copy size={14} />}
      </button>
    </header>
    <pre>{json}</pre>
  </section>;
}

export default function AgentTrace({
  trace,
  steps,
  mode,
}: {
  trace: TraceSession;
  steps: AgentTraceStep[];
  mode: TraceMode;
}) {
  const reduceMotion = useReducedMotion();
  const [selectedSequence, setSelectedSequence] = useState<number | null>(null);

  const selected = steps.find((step) => step.sequence === selectedSequence) ?? steps.at(-1);
  const traceStatus = mode === "running" ? "LIVE" : mode === "complete" ? "SYNCED" : mode === "error" ? "INTERRUPTED" : "READY";

  return <motion.section
    id="trace"
    className="trace-ledger"
    aria-labelledby="trace-title"
    initial={reduceMotion ? false : { opacity: 0, y: 18 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.45 }}
  >
    <header className="trace-heading">
      <div>
        <span className="eyebrow"><Radio size={12} /> LANGSMITH / {traceStatus}</span>
        <h3 id="trace-title">Agent handoffs<span>.</span></h3>
      </div>
      <div className="trace-identity">
        <span><i className={trace.enabled ? "connected" : ""} />{trace.enabled ? "TRACING ON" : "LOCAL TRACE"}</span>
        <code>{trace.id.slice(0, 8)}</code>
        {trace.enabled && <a href="https://smith.langchain.com" target="_blank" rel="noreferrer" title="Open LangSmith" aria-label="Open LangSmith"><ExternalLink size={15} /></a>}
      </div>
    </header>

    <div className="trace-workbench">
      <nav className="trace-rail" aria-label="Agent trace steps">
        {steps.length === 0 && <div className="trace-waiting"><span /><span /><span /></div>}
        <AnimatePresence initial={false}>
          {steps.map((step) => <motion.button
            layout
            key={step.sequence}
            type="button"
            className={selected?.sequence === step.sequence ? "selected" : ""}
            onClick={() => setSelectedSequence(step.sequence)}
            initial={reduceMotion ? false : { opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.25 }}
          >
            <span className="trace-sequence">{String(step.sequence).padStart(2, "0")}</span>
            <span className="trace-agent-name"><strong>{agentLabel(step.agent)}</strong><small>{step.agent}</small></span>
            <ArrowRight size={14} />
          </motion.button>)}
        </AnimatePresence>
      </nav>

      <div className="trace-inspector">
        {selected ? <AnimatePresence mode="wait">
          <motion.div
            key={selected.sequence}
            initial={reduceMotion ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.22 }}
          >
            <div className="trace-route">
              <span><Route size={14} /> RUN {String(selected.sequence).padStart(2, "0")}</span>
              <strong>{agentLabel(selected.agent)}</strong>
              <ArrowRight size={17} />
              <strong>{agentLabel(selected.handoff_to)}</strong>
              {selected.revision_count > 0 && <em>REV {selected.revision_count}</em>}
            </div>
            <div className="trace-payload-grid">
              <TracePayload label="Agent input" value={selected.input} />
              <TracePayload label="Agent output" value={selected.output} accent />
              <TracePayload label={selected.handoff_to ? `${agentLabel(selected.handoff_to)} input` : "Final handoff"} value={selected.next_input} />
            </div>
          </motion.div>
        </AnimatePresence> : <div className="trace-empty"><Radio size={17} /><span>{mode === "running" ? "WAITING FOR FIRST AGENT" : "NO AGENT RUNS YET"}</span></div>}
      </div>
    </div>
  </motion.section>;
}
