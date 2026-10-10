"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

type SceneProps = { active: number; complete: boolean; paused: boolean; signal: number; variant: number };
const ACCENTS = [0x486c59, 0x6f917f, 0x8baa98];
const COATINGS = [0x486c59, 0x5f806d, 0x789887];

export default function PipelineScene({ active, complete, paused, signal, variant }: SceneProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const stateRef = useRef({ active, complete, paused, signal, variant });
  const refreshRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    stateRef.current = { active, complete, paused, signal, variant };
    refreshRef.current?.();
  }, [active, complete, paused, signal, variant]);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "low-power" });
    } catch {
      mount.dataset.unavailable = "true";
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 50);
    camera.position.set(0, 0.1, 9);
    const environment = new RoomEnvironment();
    const generator = new THREE.PMREMGenerator(renderer);
    const environmentMap = generator.fromScene(environment, 0.03);
    scene.environment = environmentMap.texture;
    scene.environmentIntensity = 1.25;
    environment.dispose();
    generator.dispose();
    const key = new THREE.DirectionalLight(0xffffff, 3);
    key.position.set(-3, 4, 5);
    scene.add(key);
    const rim = new THREE.DirectionalLight(0xc5dbce, 2.5);
    rim.position.set(4, -2, 2);
    scene.add(rim);

    const assembly = new THREE.Group();
    scene.add(assembly);
    const core = new THREE.Group();
    core.rotation.set(0.25, -0.4, 0.12);
    assembly.add(core);
    const knotGeometry = new THREE.TorusKnotGeometry(1.28, 0.43, 160, 20, 2, 3);
    const chrome = new THREE.MeshStandardMaterial({ color: 0xd1d8dc, metalness: 1, roughness: 0.18 });
    const coating = new THREE.MeshStandardMaterial({ color: COATINGS[1], metalness: 0.55, roughness: 0.24 });
    const graphite = new THREE.MeshStandardMaterial({ color: 0x222427, metalness: 0.8, roughness: 0.3 });
    knotGeometry.clearGroups();
    for (const [start, count, material] of [[0, 65, 0], [65, 40, 1], [105, 19, 0], [124, 23, 2], [147, 13, 0]]) {
      knotGeometry.addGroup(start * 120, count * 120, material);
    }
    core.add(new THREE.Mesh(knotGeometry, [chrome, coating, graphite]));

    // Trace two seams on the knot surface rather than adding a postprocessing glow.
    const seams: THREE.Mesh<THREE.TubeGeometry, THREE.MeshBasicMaterial>[] = [];
    const positions = knotGeometry.getAttribute("position");
    for (const radialIndex of [3, 13]) {
      const points = Array.from({ length: 160 }, (_, index) => new THREE.Vector3().fromBufferAttribute(positions, index * 21 + radialIndex));
      const curve = new THREE.CatmullRomCurve3(points, true);
      const seam = new THREE.Mesh(new THREE.TubeGeometry(curve, 160, 0.016, 5, true), new THREE.MeshBasicMaterial({ color: 0x486c59 }));
      core.add(seam);
      seams.push(seam);
    }

    const orbit = new THREE.Group();
    orbit.rotation.set(1.08, 0.12, -0.24);
    assembly.add(orbit);
    const track = new THREE.Mesh(new THREE.TorusGeometry(3.1, 0.007, 4, 160), new THREE.MeshBasicMaterial({ color: 0x6f917f, transparent: true, opacity: 0.55 }));
    orbit.add(track);
    const nodes: THREE.Mesh<THREE.BoxGeometry, THREE.MeshStandardMaterial>[] = [];
    const arcs: THREE.Mesh<THREE.TorusGeometry, THREE.MeshBasicMaterial>[] = [];
    for (let index = 0; index < 6; index++) {
      const angle = index * Math.PI / 3;
      const arc = new THREE.Mesh(new THREE.TorusGeometry(3.1, 0.015, 4, 30, 0.54), new THREE.MeshBasicMaterial({ color: 0x486c59, transparent: true, opacity: 0.3 }));
      arc.rotation.z = angle;
      orbit.add(arc);
      arcs.push(arc);
      const node = new THREE.Mesh(new THREE.BoxGeometry(0.13, 0.33, 0.13), new THREE.MeshStandardMaterial({ color: 0xc5cdca, metalness: 0.65, roughness: 0.24, emissive: 0x486c59 }));
      node.position.set(Math.cos(angle) * 3.1, Math.sin(angle) * 3.1, 0);
      node.rotation.z = angle;
      orbit.add(node);
      nodes.push(node);
    }
    const outerOrbit = new THREE.Mesh(new THREE.TorusGeometry(3.35, 0.004, 4, 160), new THREE.MeshBasicMaterial({ color: 0x789887, transparent: true, opacity: 0.4 }));
    outerOrbit.rotation.set(-0.65, 0.3, 0.5);
    assembly.add(outerOrbit);

    const grid = new THREE.GridHelper(18, 36, 0xb8c3bd, 0xdce2de);
    grid.rotation.x = Math.PI / 2;
    grid.position.z = -4;
    grid.material.transparent = true;
    grid.material.opacity = 0.16;
    scene.add(grid);

    const pointer = { x: 0, y: 0 };
    const drag = { active: false, x: 0, y: 0, rotationX: 0, rotationY: 0 };
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const accent = new THREE.Color(0x486c59);
    const targetAccent = new THREE.Color();
    const targetCoating = new THREE.Color();
    let inView = false;
    let running = false;
    let scrolling = false;
    let elapsed = 0;
    let lastFrame = 0;
    let scrollTimer: ReturnType<typeof setTimeout> | undefined;

    const paint = () => {
      const current = stateRef.current;
      targetAccent.setHex(ACCENTS[current.variant] ?? ACCENTS[1]);
      targetCoating.setHex(COATINGS[current.variant] ?? COATINGS[1]);
      accent.lerp(targetAccent, running ? 0.09 : 1);
      coating.color.lerp(targetCoating, running ? 0.09 : 1);
      seams.forEach((seam) => seam.material.color.copy(accent));
      nodes.forEach((node, index) => {
        const lit = current.complete || index <= current.active;
        node.material.emissive.copy(accent);
        node.material.emissiveIntensity = lit ? 1.2 : 0.06;
        arcs[index].material.color.copy(accent);
        arcs[index].material.opacity = lit ? 1 : 0.24;
      });
      renderer.render(scene, camera);
    };
    const renderFrame = (now: number) => {
      if (lastFrame && now - lastFrame < 1000 / 30) return;
      if (lastFrame) elapsed += Math.min((now - lastFrame) / 1000, 0.05);
      lastFrame = now;
      const energy = stateRef.current.signal;
      core.rotation.x += ((0.25 + drag.rotationX + pointer.y * 0.12 + Math.sin(elapsed * 0.3) * 0.15) - core.rotation.x) * 0.06;
      core.rotation.y += ((-0.4 + drag.rotationY + pointer.x * 0.24 + elapsed * 0.09) - core.rotation.y) * 0.06;
      core.rotation.z = 0.12 + Math.sin(elapsed * 0.22) * 0.1;
      core.scale.setScalar(1.04 + energy * 0.045 + Math.sin(elapsed * 0.7) * 0.015);
      orbit.rotation.z += 0.0018 + energy * 0.002;
      outerOrbit.rotation.y = 0.3 + Math.sin(elapsed * 0.2) * 0.3;
      paint();
    };
    const syncLoop = () => {
      const shouldRun = inView && !scrolling && !document.hidden && !stateRef.current.paused && !preference.matches;
      if (shouldRun === running) return;
      running = shouldRun;
      lastFrame = 0;
      mount.dataset.rendering = shouldRun ? "active" : "paused";
      renderer.setAnimationLoop(shouldRun ? renderFrame : null);
    };
    mount.dataset.rendering = "paused";
    refreshRef.current = () => {
      syncLoop();
      if (inView && !running) paint();
    };
    const resize = () => {
      const width = Math.max(mount.clientWidth, 1);
      const height = Math.max(mount.clientHeight, 1);
      camera.aspect = width / height;
      camera.position.z = width < 700 ? 10.7 : 9;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height, false);
      paint();
    };
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(mount);
    resize();
    const visibilityObserver = new IntersectionObserver(([entry]) => {
      inView = entry.intersectionRatio >= 0.1;
      syncLoop();
    }, { threshold: [0, 0.1] });
    visibilityObserver.observe(mount);

    const onPointer = (event: PointerEvent) => {
      if (!inView || !running) return;
      if (drag.active) {
        drag.rotationY += (event.clientX - drag.x) * 0.008;
        drag.rotationX += (event.clientY - drag.y) * 0.008;
        drag.x = event.clientX;
        drag.y = event.clientY;
      }
      pointer.x = (event.clientX / window.innerWidth - 0.5) * 2;
      pointer.y = (event.clientY / window.innerHeight - 0.5) * 2;
    };
    const onPointerDown = (event: PointerEvent) => {
      if (event.pointerType !== "mouse" || event.button !== 0 || !running) return;
      drag.active = true;
      drag.x = event.clientX;
      drag.y = event.clientY;
      renderer.domElement.setPointerCapture(event.pointerId);
      renderer.domElement.style.cursor = "grabbing";
    };
    const onPointerUp = () => {
      drag.active = false;
      renderer.domElement.style.cursor = "";
    };
    const onScroll = () => {
      if (!inView) return;
      scrolling = true;
      syncLoop();
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(() => { scrolling = false; syncLoop(); }, 160);
    };
    window.addEventListener("pointermove", onPointer, { passive: true });
    renderer.domElement.addEventListener("pointerdown", onPointerDown);
    renderer.domElement.addEventListener("pointerup", onPointerUp);
    renderer.domElement.addEventListener("pointercancel", onPointerUp);
    window.addEventListener("scroll", onScroll, { passive: true });
    document.addEventListener("visibilitychange", syncLoop);
    preference.addEventListener("change", syncLoop);

    return () => {
      refreshRef.current = null;
      renderer.setAnimationLoop(null);
      clearTimeout(scrollTimer);
      visibilityObserver.disconnect();
      resizeObserver.disconnect();
      window.removeEventListener("pointermove", onPointer);
      renderer.domElement.removeEventListener("pointerdown", onPointerDown);
      renderer.domElement.removeEventListener("pointerup", onPointerUp);
      renderer.domElement.removeEventListener("pointercancel", onPointerUp);
      window.removeEventListener("scroll", onScroll);
      document.removeEventListener("visibilitychange", syncLoop);
      preference.removeEventListener("change", syncLoop);
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh || object instanceof THREE.LineSegments) {
          object.geometry.dispose();
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          materials.forEach((material) => material.dispose());
        }
      });
      environmentMap.dispose();
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, []);

  return <div ref={mountRef} className="pipeline-scene" aria-hidden="true"><div className="scene-fallback"><i /><i /><i /></div></div>;
}
