import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";

/**
 * VehicleTimelinePlot
 *
 * Props:
 *  frames: Array<Array<{ id: string|number, pos: [number, number], heading?: number, color?: number }>>
 *  map?: rich map (same schema you already use)
 *  metersToUnits?: number          // default 1
 *  background?: number             // default 0x0d0f13
 *  followId?: string|number|null   // camera follows this vehicle if present
 *  fps?: number                    // default 20
 *  loop?: boolean                  // default false
 *  startPaused?: boolean           // default false
 *  onPlayStateChange?: (isPlaying:boolean)=>void
 */
export default function VehicleTimelinePlot({
  frames = [],
  map = null,
  metersToUnits = 1,
  background = 0x0d0f13,
  followId = null,
  fps = 20,
  loop = false,
  startPaused = false,
  onPlayStateChange,
}) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const frameReqRef = useRef(null);

  // data & objects
  const mapGroupRef = useRef(null);
  const meshesRef = useRef(new Map()); // id -> { mesh, geo, mat }

  // playback
  const [isPlaying, setIsPlaying] = useState(!startPaused);
  const [frameIndex, setFrameIndex] = useState(0);
  const lastTickRef = useRef(0);
  const followRef = useRef(followId);

  // keep latest followId for RAF loop
  useEffect(() => { followRef.current = followId; }, [followId]);

  // init scene once
  useEffect(() => {
    const mount = mountRef.current;
    const width = mount?.clientWidth || 600;
    const height = mount?.clientHeight || 400;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(background);

    // camera (ortho, top-down)
    const viewSize = 60;
    const aspect = width / height;
    const camera = new THREE.OrthographicCamera(
      -viewSize * aspect,
      viewSize * aspect,
      viewSize,
      -viewSize,
      0.1,
      1000
    );
    camera.position.set(0, 0, 100);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height);

    mount.innerHTML = "";
    mount.appendChild(renderer.domElement);

    // grid (optional—kept for context)
    const grid = new THREE.GridHelper(400, 40, 0x444444, 0x222222);
    grid.rotation.x = Math.PI / 2;
    grid.renderOrder = 0;
    scene.add(grid);

    // map group
    const mapGroup = new THREE.Group();
    mapGroup.renderOrder = 1;
    scene.add(mapGroup);

    sceneRef.current = scene;
    cameraRef.current = camera;
    rendererRef.current = renderer;
    mapGroupRef.current = mapGroup;

    // initial map draw if provided
    if (map) {
      drawRichMap(map, mapGroup, metersToUnits);
    }

    // resize
    const onResize = () => {
      const w = mount.clientWidth || width;
      const h = mount.clientHeight || height;
      const asp = w / h;
      camera.left = -viewSize * asp;
      camera.right = viewSize * asp;
      camera.top = viewSize;
      camera.bottom = -viewSize;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      renderOnce();
    };
    window.addEventListener("resize", onResize);

    // start RAF
    lastTickRef.current = performance.now();
    frameReqRef.current = requestAnimationFrame(tick);

    function tick(now) {
      const renderer = rendererRef.current;
      const camera = cameraRef.current;
      const scene = sceneRef.current;
      if (!renderer || !camera || !scene) return;

      const dt = now - lastTickRef.current;
      const frameDuration = 1000 / Math.max(1, fps);

      if (isPlaying && dt >= frameDuration && frames.length > 0) {
        lastTickRef.current = now - (dt % frameDuration);
        // advance frame
        setFrameIndex((prev) => {
          let next = prev + 1;
          if (next >= frames.length) {
            next = loop ? 0 : frames.length - 1;
            if (!loop) {
              // auto-pause at the end if not looping
              setIsPlaying(false);
              onPlayStateChange?.(false);
            }
          }
          return next;
        });
      }

      // render current frame (without changing state again)
      renderOnce();
      frameReqRef.current = requestAnimationFrame(tick);
    }

    return () => {
      if (frameReqRef.current) cancelAnimationFrame(frameReqRef.current);
      window.removeEventListener("resize", onResize);

      // dispose meshes
      for (const [, rec] of meshesRef.current.entries()) {
        scene.remove(rec.mesh);
        rec.geo.dispose();
        rec.mat.dispose();
      }
      meshesRef.current.clear();

      // dispose map
      if (mapGroupRef.current) {
        mapGroupRef.current.children.forEach((obj) => {
          if (obj.geometry) obj.geometry.dispose();
          if (obj.material) obj.material.dispose();
        });
        scene.remove(mapGroupRef.current);
        mapGroupRef.current = null;
      }

      renderer.dispose();
      if (renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [background, metersToUnits, fps, loop, startPaused, map]);

  // redraw map if it changes (or scale changes)
  useEffect(() => {
    if (!mapGroupRef.current) return;
    // clear & redraw
    mapGroupRef.current.children.forEach((obj) => {
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) obj.material.dispose();
    });
    mapGroupRef.current.clear();
    if (map) drawRichMap(map, mapGroupRef.current, metersToUnits);
    renderOnce();
  }, [map, metersToUnits]);

  // whenever frameIndex changes, upsert/remove vehicle meshes & update transforms
  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return;

    const current = frames[frameIndex] || [];
    const wantIds = new Set(current.map((v) => String(v.id)));

    // upsert
    for (const v of current) {
      const idKey = String(v.id);
      if (!meshesRef.current.has(idKey)) {
        const geo = new THREE.BoxGeometry(4, 2, 1);
        const mat = new THREE.MeshBasicMaterial({ color: v.color ?? 0xff3b30 });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(0, 0, 1.0);
        scene.add(mesh);
        meshesRef.current.set(idKey, { mesh, geo, mat });
      }
    }

    // remove stale
    for (const [idKey, rec] of meshesRef.current.entries()) {
      if (!wantIds.has(idKey)) {
        scene.remove(rec.mesh);
        rec.geo.dispose();
        rec.mat.dispose();
        meshesRef.current.delete(idKey);
      }
    }

    // update transforms/colors for current frame
    for (const v of current) {
      const idKey = String(v.id);
      const rec = meshesRef.current.get(idKey);
      if (!rec) continue;
      const [x, y] = v.pos;
      rec.mesh.position.set(x * metersToUnits, y * metersToUnits, 1.0);
      if (v.heading !== undefined) rec.mesh.rotation.z = v.heading;
      if (v.color != null) rec.mat.color.setHex(v.color);
    }

    // follow camera
    if (followRef.current != null) {
      const fidKey = String(followRef.current);
      const rec = meshesRef.current.get(fidKey);
      if (rec) {
        cameraRef.current.position.x = rec.mesh.position.x;
        cameraRef.current.position.y = rec.mesh.position.y;
        cameraRef.current.updateMatrixWorld();
      }
    }

    renderOnce();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [frameIndex, frames, metersToUnits, followId]);

  // controls
  const togglePlay = () => {
    setIsPlaying((p) => {
      const next = !p;
      onPlayStateChange?.(next);
      // re-sync tick pacing
      lastTickRef.current = performance.now();
      return next;
    });
  };

  const renderOnce = () => {
    const renderer = rendererRef.current;
    const camera = cameraRef.current;
    const scene = sceneRef.current;
    if (!renderer || !camera || !scene) return;
    renderer.render(scene, camera);
  };

  return (
    <div style={{ position: "relative" }}>
      <div
        ref={mountRef}
        style={{
          width: "100%",
          height: 400,
          borderRadius: 12,
          overflow: "hidden",
          background: "#0d0f13",
        }}
      />
      {/* Controls */}
      <div
        style={{
          position: "absolute",
          left: 12,
          bottom: 12,
          display: "flex",
          gap: 8,
          background: "rgba(0,0,0,0.5)",
          padding: "8px 10px",
          borderRadius: 8,
          alignItems: "center",
        }}
      >
        <button
          onClick={togglePlay}
          style={{
            padding: "6px 12px",
            borderRadius: 6,
            border: "1px solid #444",
            background: isPlaying ? "#ef4444" : "#10b981",
            color: "white",
            cursor: "pointer",
          }}
        >
          {isPlaying ? "Pause" : "Play"}
        </button>
        <span style={{ color: "#e5e7eb", fontSize: 12 }}>
          Frame {frames.length ? frameIndex + 1 : 0}/{frames.length || 0}
        </span>
      </div>
    </div>
  );
}

/* ---------- helper to draw your rich map ---------- */
function drawRichMap(mapObj, group, metersToUnits) {
  const features = mapObj?.features || [];
  const defaultLaneColor = 0x9aa0a6;

  for (const f of features) {
    const pts = (f.polyline || []).map(([x, y]) =>
      new THREE.Vector3(x * metersToUnits, y * metersToUnits, 0.02)
    );
    if (pts.length < 2) continue;

    const geo = new THREE.BufferGeometry().setFromPoints(pts);

    if (f.kind === "lane") {
      const mat = new THREE.LineBasicMaterial({
        color: defaultLaneColor,
        transparent: true,
        opacity: 0.7,
        depthWrite: false,
      });
      const line = new THREE.Line(geo, mat);
      line.renderOrder = 1;
      group.add(line);
      continue;
    }

    const colorHex = f.style?.color || "#FFFFFF";
    const color = new THREE.Color(colorHex);
    const pattern = f.style?.pattern || "solid";

    if (pattern === "dashed") {
      const dashSize = 1.0 * metersToUnits;
      const gapSize = 1.0 * metersToUnits;
      const mat = new THREE.LineDashedMaterial({
        color,
        transparent: true,
        opacity: 0.95,
        dashSize,
        gapSize,
        depthWrite: false,
      });
      const line = new THREE.Line(geo, mat);
      line.computeLineDistances();
      line.renderOrder = 2;
      group.add(line);
    } else {
      const mat = new THREE.LineBasicMaterial({
        color,
        transparent: true,
        opacity: 0.95,
        depthWrite: false,
      });
      const line = new THREE.Line(geo, mat);
      line.renderOrder = 2;
      group.add(line);
    }
  }
}
