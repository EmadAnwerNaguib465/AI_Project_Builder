"use client";

import { useEffect, useState } from "react";
import { ArrowUpRight, Check, Download, FileText, Printer, RotateCcw } from "lucide-react";
import ReactMarkdown from "react-markdown";
import type { ProjectReport } from "@/lib/types";

const SECTIONS = ["Overview", "Architecture", "Dataset", "Model", "Roadmap", "Sources"] as const;
type Section = (typeof SECTIONS)[number];

function Markdown({ children, allowedUrls }: { children: string; allowedUrls?: string[] }) {
  return <div className="report-markdown"><ReactMarkdown components={{
    a: ({ href, children: content }) => href && (href.startsWith("https://") || href.startsWith("http://")) && (!allowedUrls || allowedUrls.includes(href))
      ? <a href={href} target="_blank" rel="noopener noreferrer">{content}<ArrowUpRight size={13} aria-hidden="true" /></a>
      : <span>{content}</span>,
  }}>{children}</ReactMarkdown></div>;
}

export default function ReportView({ report, onReset }: { report: ProjectReport; onReset: () => void }) {
  const [activeSection, setActiveSection] = useState<Section>("Overview");
  const [exportingPdf, setExportingPdf] = useState(false);
  const datasets = (report.dataset_recommendations ?? []).filter((dataset) => dataset.url.startsWith("https://"));

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      const overview = document.getElementById("report-overview");
      if (overview && overview.getBoundingClientRect().top > 80) {
        setActiveSection("Overview");
        return;
      }
      const visible = entries.find((entry) => entry.isIntersecting);
      const section = SECTIONS.find((item) => visible?.target.id === `report-${item.toLowerCase()}`);
      if (section) setActiveSection(section);
    }, { rootMargin: "-80px 0px -65% 0px" });
    SECTIONS.forEach((section) => {
      const element = document.getElementById(`report-${section.toLowerCase()}`);
      if (element) observer.observe(element);
    });
    return () => observer.disconnect();
  }, []);

  const download = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${report.project_title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "project-plan"}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const downloadPdf = async () => {
    try {
      setExportingPdf(true);
      const res = await fetch("/api/export-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(report),
      });
      if (!res.ok) {
        window.print();
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${report.project_title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "project-plan"}.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch {
      window.print();
    } finally {
      setExportingPdf(false);
    }
  };

  return <section className="report-view" aria-labelledby="report-title">
    <div className="report-topline"><span className="eyebrow">03 / YOUR BLUEPRINT</span><span className="report-ready"><Check size={13} /> READY TO BUILD</span></div>
    <div className="report-heading-row">
      <div><h2 id="report-title">{report.project_title}</h2><p>{report.executive_summary}</p></div>
      <div className="report-actions">
        <button type="button" className="icon-action" onClick={downloadPdf} disabled={exportingPdf} title="Download PDF" aria-label="Download PDF"><FileText size={18} /></button>
        <button type="button" className="icon-action" onClick={() => window.print()} title="Print / Save PDF" aria-label="Print / Save PDF"><Printer size={18} /></button>
        <button type="button" className="icon-action" onClick={download} title="Download JSON" aria-label="Download JSON"><Download size={18} /></button>
        <button type="button" className="icon-action" onClick={onReset} title="New plan" aria-label="New plan"><RotateCcw size={18} /></button>
      </div>
    </div>

    <div className="report-metrics">
      <div><strong>{report.estimated_timeline_weeks}<small>w</small></strong><span>Estimated timeline</span></div>
      <div><strong>{report.implementation_roadmap.length}</strong><span>Build steps</span></div>
      <div><strong>{report.sources.length}</strong><span>Sources</span></div>
      <div><strong>{report.revision_count}</strong><span>Review cycles</span></div>
    </div>

    <nav className="report-nav" aria-label="Report sections">
      {SECTIONS.map((section) => <a key={section} href={`#report-${section.toLowerCase()}`} aria-current={activeSection === section ? "location" : undefined} onClick={() => setActiveSection(section)}>{section}</a>)}
    </nav>

    <section className="report-section" id="report-overview" aria-labelledby="report-overview-title">
      <h3 id="report-overview-title">Overview</h3>
      <div className="overview-grid">
        <div className="report-block"><h4>Objectives</h4><ol className="numbered-list">{report.objectives.map((item, index) => <li key={`${item}-${index}`}><span>{String(index + 1).padStart(2, "0")}</span>{item}</li>)}</ol></div>
        <div className="report-block"><h4>Success metrics</h4><ul className="bullet-list">{report.success_metrics.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul></div>
        <div className="report-block"><h4>Required skills</h4><div className="tag-list">{report.required_skills.map((item, index) => <span key={`${item}-${index}`}>{item}</span>)}</div></div>
        <div className="report-block"><h4>Recommended tools</h4><div className="tag-list">{report.recommended_tools.map((item, index) => <span key={`${item}-${index}`}>{item}</span>)}</div></div>
      </div>
    </section>
    <section className="report-section" id="report-architecture" aria-labelledby="report-architecture-title">
      <h3 id="report-architecture-title">Architecture</h3>
      <div className="prose-block"><Markdown>{report.technical_architecture}</Markdown></div>
    </section>
    <section className="report-section" id="report-dataset" aria-labelledby="report-dataset-title">
      <h3 id="report-dataset-title">Dataset strategy</h3>
      <div className="prose-block">
        <div className="dataset-heading"><h4>Recommended datasets</h4><span>{datasets.length} {datasets.length === 1 ? "source" : "sources"}</span></div>
        <p className="dataset-note">{report.dataset_discovery_note || (datasets.length ? "Dataset candidates from catalog and search results. Review the source terms before use." : "No source-backed dataset recommendations are available for this plan.")}</p>
        {datasets.length > 0 && <ul className="dataset-list">{datasets.map((dataset) => <li className="dataset-recommendation" key={dataset.url}>
          <div className="dataset-card-heading"><div><span className="dataset-provider">{dataset.provider}</span><h4>{dataset.name}</h4></div><a href={dataset.url} target="_blank" rel="noopener noreferrer" className="dataset-link" aria-label={`Open ${dataset.name} dataset`}><span>Open dataset</span><ArrowUpRight size={17} /></a></div>
          <p className="dataset-description">{dataset.description}</p>
          <div className="dataset-fit"><strong>Project fit</strong><p>{dataset.relevance}</p></div>
          <dl className="dataset-metadata">{[["Data type", dataset.data_type], ["Size / range", dataset.size], ["License", dataset.license], ["Access", dataset.access]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value || "Not provided by source"}</dd></div>)}</dl>
          <span className="dataset-provenance">Found via {dataset.discovery_source}</span>
        </li>)}</ul>}
        <Markdown allowedUrls={datasets.map((dataset) => dataset.url)}>{report.dataset_plan}</Markdown>
      </div>
    </section>
    <section className="report-section" id="report-model" aria-labelledby="report-model-title">
      <h3 id="report-model-title">Model strategy</h3>
      <div className="prose-block"><Markdown>{report.model_plan}</Markdown></div>
    </section>
    <section className="report-section" id="report-roadmap" aria-labelledby="report-roadmap-title">
      <h3 id="report-roadmap-title">Roadmap</h3>
      <div className="roadmap-layout"><div className="report-block"><h4>Implementation roadmap</h4><ol className="roadmap-list">{report.implementation_roadmap.map((item, index) => <li key={`${item}-${index}`}><span>{String(index + 1).padStart(2, "0")}</span><p>{item}</p></li>)}</ol></div><div className="report-block risks"><h4>Risks & mitigations</h4><ul className="bullet-list">{report.risks_and_mitigations.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul></div></div>
    </section>
    <section className="report-section" id="report-sources" aria-labelledby="report-sources-title">
      <h3 id="report-sources-title">Research sources</h3>
      {report.sources.length ? <ul className="source-list">{report.sources.map((source, index) => <li key={`${source}-${index}`}><span>{String(index + 1).padStart(2, "0")}</span>{/^https?:\/\//.test(source) ? <a href={source} target="_blank" rel="noopener noreferrer">{source}<ArrowUpRight size={15} aria-hidden="true" /></a> : <span>{source}</span>}</li>)}</ul> : <p>No sources were collected for this plan.</p>}
    </section>
  </section>;
}
