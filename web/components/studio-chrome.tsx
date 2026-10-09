"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUpRight, Asterisk, Menu, X } from "lucide-react";

export function Intro() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    const hide = () => { element.hidden = true; };
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) { hide(); return; }
    try { if (sessionStorage.getItem("studio-intro")) { hide(); return; } sessionStorage.setItem("studio-intro", "seen"); } catch { /* The intro also works without browser storage. */ }
    let frame = 0;
    let timeout: ReturnType<typeof setTimeout>;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min((now - start) / 1300, 1);
      const progress = Math.round((t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2) * 100);
      element.querySelector("output")!.textContent = String(progress).padStart(3, "0");
      element.style.setProperty("--progress", `${progress}%`);
      if (t < 1) frame = requestAnimationFrame(tick);
      else { element.classList.add("leaving"); timeout = setTimeout(hide, 650); }
    };
    frame = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(frame); clearTimeout(timeout); };
  }, []);
  return <div ref={ref} className="intro" aria-hidden="true"><div className="intro-brand"><Asterisk size={36} /> AI Project Builder</div><p>From a bold idea to a considered plan.</p><div className="intro-progress"><i /><span>THE PROJECT STUDIO <output>000</output></span></div></div>;
}

function Clock() {
  const [clock, setClock] = useState("");
  useEffect(() => {
    const tick = () => setClock(new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit" }).format(new Date()).toLowerCase());
    const timer = setInterval(tick, 1000);
    tick();
    return () => clearInterval(timer);
  }, []);
  return <span className="clock"><span>Local time</span><time>{clock || "--:--"}</time></span>;
}

export function StudioHeader({ hasReport }: { hasReport: boolean }) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const menuRef = useRef<HTMLButtonElement>(null);
  const previousOverflow = useRef("");
  const links = [["Workspace", "workspace"], ["Project ideas", "ideas"], ["The process", "pipeline"], ...(hasReport ? [["Your blueprint", "blueprint"]] : [])];
  const unlock = () => { document.documentElement.style.overflow = previousOverflow.current; menuRef.current?.focus({ preventScroll: true }); };
  const close = () => { dialogRef.current?.close(); unlock(); };
  useEffect(() => () => { if (dialogRef.current?.open) document.documentElement.style.overflow = previousOverflow.current; }, []);
  return <>
    <a className="skip-link" href="#idea">Skip to project brief</a>
    <header className="topbar shell">
      <a className="brand" href="#workspace"><Asterisk size={28} /><span>AI Project Builder<span className="brand-dot">.</span></span></a>
      <nav className="top-nav" aria-label="Workspace navigation"><a href="#workspace">Workspace</a><a href="#ideas">Project ideas</a><a href="#pipeline">Process</a></nav>
      <div className="top-actions"><Clock /><button ref={menuRef} type="button" className="menu-trigger icon-action" aria-label="Open menu" aria-haspopup="dialog" onClick={() => { previousOverflow.current = document.documentElement.style.overflow; document.documentElement.style.overflow = "hidden"; dialogRef.current?.showModal(); }}><Menu size={19} /></button></div>
    </header>
    <dialog ref={dialogRef} className="nav-dialog" onClose={unlock} aria-label="Site navigation">
      <div className="shell menu-shell"><div className="menu-top"><span className="brand"><Asterisk size={28} />AI Project Builder.</span><button type="button" className="icon-action" onClick={close} aria-label="Close menu" title="Close menu"><X size={22} /></button></div>
        <nav>{links.map(([label, id], index) => <a key={id} href={`#${id}`} onClick={close} style={{ animationDelay: `${index * 70}ms` }}><span>0{index + 1}</span>{label}<ArrowUpRight /></a>)}</nav>
        <div className="menu-bottom"><Clock /><span>FROM AN IDEA. TO A BLUEPRINT.</span></div>
      </div>
    </dialog>
  </>;
}
