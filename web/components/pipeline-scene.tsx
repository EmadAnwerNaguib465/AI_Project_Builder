"use client";

import Image from "next/image";
import { useEffect, useRef } from "react";
import * as THREE from "three";

export default function PipelineScene({ paused }: { paused: boolean }) {
  const hostRef = useRef<HTMLDivElement>(null);
  const pausedRef = useRef(paused);
  pausedRef.current = paused;

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
    renderer.toneMappingExposure = 1.08;
    host.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 30);
    camera.position.set(0, 0, 5.9);
    const icon = new THREE.Group();
    scene.add(icon);

    scene.add(new THREE.HemisphereLight(0xf5fff7, 0x405e50, 2.4));
    const keyLight = new THREE.DirectionalLight(0xffffff, 3.2);
    keyLight.position.set(-2.8, 3.8, 5);
    scene.add(keyLight);
    const edgeLight = new THREE.PointLight(0xc3816d, 15, 9);
    edgeLight.position.set(2.4, -1.8, 2.3);
    scene.add(edgeLight);

    const coin = new THREE.Mesh(
      new THREE.CylinderGeometry(1.08, 1.08, 0.16, 96, 1, false),
      new THREE.MeshPhysicalMaterial({ color: 0x466c58, metalness: 0.7, roughness: 0.27, clearcoat: 0.9, clearcoatRoughness: 0.2 }),
    );
    coin.rotation.x = Math.PI / 2;
    icon.add(coin);

    const faceMaterial = new THREE.MeshStandardMaterial({ color: 0xe8efea, metalness: 0.18, roughness: 0.34, side: THREE.DoubleSide });
    const frontFace = new THREE.Mesh(new THREE.CircleGeometry(1.045, 96), faceMaterial);
    frontFace.position.z = 0.082;
    icon.add(frontFace);
    const backFace = new THREE.Mesh(new THREE.CircleGeometry(1.045, 96), faceMaterial);
    backFace.position.z = -0.082;
    icon.add(backFace);

    const rimMaterial = new THREE.MeshStandardMaterial({ color: 0xc3816d, metalness: 0.82, roughness: 0.22 });
    const rim = new THREE.Mesh(new THREE.TorusGeometry(1.065, 0.022, 10, 96), rimMaterial);
    rim.position.z = 0.091;
    icon.add(rim);
    const backRim = new THREE.Mesh(new THREE.TorusGeometry(1.065, 0.022, 10, 96), rimMaterial);
    backRim.position.z = -0.091;
    icon.add(backRim);

    const iconMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, toneMapped: false, side: THREE.DoubleSide, depthWrite: false });
    const iconGeometry = new THREE.PlaneGeometry(1.56, 1.59);
    const frontIcon = new THREE.Mesh(iconGeometry, iconMaterial);
    frontIcon.position.z = 0.105;
    icon.add(frontIcon);
    const backIcon = new THREE.Mesh(iconGeometry, iconMaterial);
    backIcon.position.z = -0.105;
    backIcon.rotation.y = Math.PI;
    icon.add(backIcon);

    let animationFrame = 0;
    let startedAt = performance.now();
    const loader = new THREE.TextureLoader();
    const markTexture = loader.load("/logo-mark.png", (texture) => {
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
      iconMaterial.map = texture;
      iconMaterial.needsUpdate = true;
    });

    const resize = () => {
      const width = Math.max(host.clientWidth, 1);
      const height = Math.max(host.clientHeight, 1);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.position.z = width < 620 ? 6.3 : 5.9;
      camera.updateProjectionMatrix();
      icon.scale.setScalar(Math.min(1, width / 420));
      renderer.render(scene, camera);
    };
    const observer = new ResizeObserver(resize);
    observer.observe(host);
    resize();

    const animate = (now: number) => {
      animationFrame = requestAnimationFrame(animate);
      if (pausedRef.current) {
        startedAt = now;
        return;
      }
      const secondsPerTurn = 9;
      icon.rotation.y = ((now - startedAt) / 1000 / secondsPerTurn) * Math.PI * 2;
      renderer.render(scene, camera);
    };
    animationFrame = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationFrame);
      observer.disconnect();
      markTexture.dispose();
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

  return <div ref={hostRef} className="pipeline-scene" data-rendering={paused ? "paused" : "active"} aria-label="3D Planorai logo icon rotating 360 degrees" role="img">
    <div className="scene-logo-fallback"><Image src="/logo-mark.png" alt="Planorai logo icon" width={357} height={364} /></div>
  </div>;
}
