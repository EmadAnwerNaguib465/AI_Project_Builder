"use client";

import Image from "next/image";
import { useEffect, useRef } from "react";
import * as THREE from "three";

type Props = { active: number; complete: boolean; paused: boolean; signal: number; variant: number };

function roundedCard(width: number, height: number, radius: number) {
  const shape = new THREE.Shape();
  shape.moveTo(-width / 2 + radius, -height / 2);
  shape.lineTo(width / 2 - radius, -height / 2);
  shape.quadraticCurveTo(width / 2, -height / 2, width / 2, -height / 2 + radius);
  shape.lineTo(width / 2, height / 2 - radius);
  shape.quadraticCurveTo(width / 2, height / 2, width / 2 - radius, height / 2);
  shape.lineTo(-width / 2 + radius, height / 2);
  shape.quadraticCurveTo(-width / 2, height / 2, -width / 2, height / 2 - radius);
  shape.lineTo(-width / 2, -height / 2 + radius);
  shape.quadraticCurveTo(-width / 2, -height / 2, -width / 2 + radius, -height / 2);
  return new THREE.ExtrudeGeometry(shape, { depth: 0.16, bevelEnabled: true, bevelSegments: 4, steps: 1, bevelSize: 0.025, bevelThickness: 0.025, curveSegments: 8 });
}

export default function PipelineScene({ active, complete, paused, signal, variant }: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const pausedRef = useRef(paused);
  const valuesRef = useRef({ active, complete, signal, variant });
  pausedRef.current = paused;
  valuesRef.current = { active, complete, signal, variant };

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "low-power" });
    } catch {
      host.dataset.unavailable = "true";
      return;
    }

    host.dataset.unavailable = "false";
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.6));
    renderer.setClearColor(0x000000, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.12;
    host.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 40);
    camera.position.set(0, 0, 6.5);
    const group = new THREE.Group();
    scene.add(group);

    scene.add(new THREE.HemisphereLight(0xf6fff8, 0x728478, 2.0));
    const keyLight = new THREE.DirectionalLight(0xffffff, 3.2);
    keyLight.position.set(-3.5, 4.5, 6);
    scene.add(keyLight);
    const rimLight = new THREE.PointLight(0xd3a08a, 18, 12);
    rimLight.position.set(3, -1.7, 2.5);
    scene.add(rimLight);

    const cardWidth = 4.55;
    const cardHeight = 1.28;
    const card = new THREE.Mesh(
      roundedCard(cardWidth, cardHeight, 0.16),
      new THREE.MeshPhysicalMaterial({ color: 0xe7eeea, metalness: 0.22, roughness: 0.3, clearcoat: 0.85, clearcoatRoughness: 0.2 }),
    );
    card.position.z = -0.11;
    group.add(card);

    const logoMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, toneMapped: false, side: THREE.DoubleSide, depthWrite: false });
    const logo = new THREE.Mesh(new THREE.PlaneGeometry(cardWidth - 0.1, cardHeight - 0.1), logoMaterial);
    logo.position.z = 0.075;
    group.add(logo);

    const halo = new THREE.Mesh(
      new THREE.TorusGeometry(1.72, 0.008, 6, 160),
      new THREE.MeshBasicMaterial({ color: 0x769985, transparent: true, opacity: 0.38 }),
    );
    halo.scale.set(1.42, 0.48, 1);
    halo.position.z = -0.34;
    group.add(halo);
    const haloInner = new THREE.Mesh(
      new THREE.TorusGeometry(1.65, 0.006, 6, 160),
      new THREE.MeshBasicMaterial({ color: 0xc3816d, transparent: true, opacity: 0.3 }),
    );
    haloInner.scale.set(1.4, 0.44, 1);
    haloInner.rotation.z = -0.18;
    haloInner.position.z = -0.3;
    group.add(haloInner);

    const nodes: THREE.Mesh[] = [];
    const nodePositions = [-2.55, -1.55, -0.52, 0.52, 1.55, 2.55];
    nodePositions.forEach((x, index) => {
      const material = new THREE.MeshStandardMaterial({ color: index === 4 ? 0xbd715f : 0x648671, metalness: 0.52, roughness: 0.25, emissive: 0x365344, emissiveIntensity: 0.3 });
      const node = new THREE.Mesh(new THREE.SphereGeometry(index === 0 || index === 5 ? 0.075 : 0.045, 20, 16), material);
      node.position.set(x, index % 2 === 0 ? -0.83 : 0.83, -0.06);
      group.add(node);
      nodes.push(node);
    });

    let logoTexture: THREE.CanvasTexture | null = null;
    let frame = 0;
    let startedAt = performance.now();
    const loader = new THREE.TextureLoader();
    const textureRequest = loader.load("/logo.png", (source) => {
      const image = source.image as HTMLImageElement;
      const width = image.naturalWidth || image.width;
      const height = image.naturalHeight || image.height;
      const canvas = document.createElement("canvas");
      canvas.width = 1024;
      canvas.height = 320;
      const context = canvas.getContext("2d", { willReadFrequently: true });
      if (!context) return;
      context.drawImage(image, width * 0.14, height * 0.235, width * 0.72, height * 0.35, 0, 0, canvas.width, canvas.height);
      const pixels = context.getImageData(0, 0, canvas.width, canvas.height);
      const { data } = pixels;
      const bg = [data[0], data[1], data[2]];
      for (let i = 0; i < data.length; i += 4) {
        const delta = Math.max(Math.abs(data[i] - bg[0]), Math.abs(data[i + 1] - bg[1]), Math.abs(data[i + 2] - bg[2]));
        if (delta < 10) data[i + 3] = 0;
        else if (delta < 42) data[i + 3] = Math.round(data[i + 3] * ((delta - 10) / 32));
      }
      context.putImageData(pixels, 0, 0);
      logoTexture = new THREE.CanvasTexture(canvas);
      logoTexture.colorSpace = THREE.SRGBColorSpace;
      logoTexture.anisotropy = renderer.capabilities.getMaxAnisotropy();
      logoMaterial.map = logoTexture;
      logoMaterial.needsUpdate = true;
    });

    const resize = () => {
      const width = Math.max(host.clientWidth, 1);
      const height = Math.max(host.clientHeight, 1);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.position.z = width < 620 ? 7.2 : 6.5;
      camera.updateProjectionMatrix();
      const fit = Math.min(1, width / 560);
      group.scale.setScalar(fit);
      renderer.render(scene, camera);
    };
    const observer = new ResizeObserver(resize);
    observer.observe(host);
    resize();

    const animate = (now: number) => {
      frame = requestAnimationFrame(animate);
      if (pausedRef.current) {
        startedAt = now;
        return;
      }
      const elapsed = (now - startedAt) / 1000;
      const values = valuesRef.current;
      const phase = values.variant * 0.42;
      const strength = values.complete ? 1 : values.active >= 0 ? 0.75 : 0.45;
      group.rotation.y = Math.sin(elapsed * 0.54 + phase) * 0.11;
      group.rotation.x = Math.sin(elapsed * 0.7 + phase) * 0.035;
      group.rotation.z = Math.sin(elapsed * 0.38 + phase) * 0.018;
      group.position.y = Math.sin(elapsed * 0.9 + phase) * 0.075;
      keyLight.intensity = 2.7 + strength + Math.min(values.signal, 1) * 0.4;
      nodes.forEach((node, index) => {
        const material = node.material as THREE.MeshStandardMaterial;
        const activeNode = values.complete || index <= values.active;
        material.emissiveIntensity = activeNode ? 0.65 + Math.sin(elapsed * 2.4 + index) * 0.18 : 0.12;
      });
      renderer.render(scene, camera);
    };
    frame = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      textureRequest.dispose();
      logoTexture?.dispose();
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh) {
          object.geometry.dispose();
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          materials.forEach((material) => material.dispose());
        }
      });
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);

  return <div ref={hostRef} className="pipeline-scene" data-rendering={paused ? "paused" : "active"} aria-label="Animated 3D Planorai logo" role="img">
    <div className="scene-logo-fallback"><Image src="/logo.png" alt="Planorai" width={1774} height={1024} /></div>
  </div>;
}
