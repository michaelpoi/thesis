import React, { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

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
  startIndex = 0,
}) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const frameReqRef = useRef(null);

  const mapGroupRef = useRef(null);
  const meshesRef = useRef(new Map());

  // NEW: goal visuals per vehicle: id -> { rect?: {mesh,geo,mat}, sigRect?: string }
  const goalsRef = useRef(new Map());

  const [isPlaying, setIsPlaying] = useState(!startPaused);
  const isPlayingRef = useRef(!startPaused);
  useEffect(() => { isPlayingRef.current = isPlaying; }, [isPlaying]);

  const lastTickRef = useRef(0);
  const followRef = useRef(followId);
  useEffect(() => { followRef.current = followId; }, [followId]);

  // 1) normalize frames and KEEP goal
  const framesNorm = useMemo(() => normalizeFrames(frames), [frames]);

  // 2) slice visible part
  const effectiveStart = useMemo(() => {
    if (!framesNorm.length) return 0;
    const s = Number.isFinite(startIndex) ? Math.max(0, Math.min(startIndex, framesNorm.length - 1)) : 0;
    return s;
  }, [startIndex, framesNorm.length]);

  const visibleFrames = useMemo(
    () => framesNorm.slice(effectiveStart),
    [framesNorm, effectiveStart]
  );

  const [frameIndex, setFrameIndex] = useState(0);

  useEffect(() => {
    setFrameIndex(0);
    lastTickRef.current = performance.now();
  }, [effectiveStart, visibleFrames.length]);

  /* ---------- init scene ---------- */
  useEffect(() => {
    const mount = mountRef.current;
    const width = mount?.clientWidth || 600;
    const height = mount?.clientHeight || 400;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(background);

    const viewSize = 60;
    const aspect = width / height;
    const camera = new THREE.OrthographicCamera(
      -viewSize * aspect, viewSize * aspect, viewSize, -viewSize, 0.1, 1000
    );
    camera.position.set(0, 0, 100);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height);

    mount.innerHTML = "";
    mount.appendChild(renderer.domElement);

    const grid = new THREE.GridHelper(400, 40, 0x444444, 0x222222);
    grid.rotation.x = Math.PI / 2;
    grid.renderOrder = 0;
    scene.add(grid);

    const mapGroup = new THREE.Group();
    mapGroup.renderOrder = 1;
    scene.add(mapGroup);

    sceneRef.current = scene;
    cameraRef.current = camera;
    rendererRef.current = renderer;
    mapGroupRef.current = mapGroup;

    if (map) drawRichMap(map, mapGroup, metersToUnits);

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

    lastTickRef.current = performance.now();
    frameReqRef.current = requestAnimationFrame(tick);

    function tick(now) {
      const renderer = rendererRef.current;
      const camera = cameraRef.current;
      const scene = sceneRef.current;
      if (!renderer || !camera || !scene) return;

      const dt = now - lastTickRef.current;
      const frameDuration = 1000 / Math.max(1, fps);

      if (isPlayingRef.current && dt >= frameDuration && visibleFrames.length > 0) {
        lastTickRef.current = now - (dt % frameDuration);
        setFrameIndex(prev => {
          let next = prev + 1;
          if (next === visibleFrames.length - 1) {
            isPlayingRef.current = false;
            setIsPlaying(false);
            onPlayStateChange?.(false);
          }
          if (next >= visibleFrames.length) {
            next = loop ? 0 : visibleFrames.length - 1;
            if (!loop) {
              isPlayingRef.current = false;
              setIsPlaying(false);
              onPlayStateChange?.(false);
            }
          }
          return next;
        });
      }

      renderOnce();
      frameReqRef.current = requestAnimationFrame(tick);
    }

    return () => {
      if (frameReqRef.current) cancelAnimationFrame(frameReqRef.current);
      window.removeEventListener("resize", onResize);

      for (const [, rec] of meshesRef.current.entries()) {
        scene.remove(rec.mesh);
        rec.geo.dispose();
        rec.mat.dispose();
      }
      meshesRef.current.clear();

      for (const [, rec] of goalsRef.current.entries()) {
        if (rec.rect) {
          scene.remove(rec.rect.mesh);
          rec.rect.geo.dispose();
          rec.rect.mat.dispose();
        }
      }
      goalsRef.current.clear();

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
  }, [background, metersToUnits, fps, loop, startPaused, map, visibleFrames.length]);

  /* ---------- redraw map on change ---------- */
  useEffect(() => {
    if (!mapGroupRef.current) return;
    mapGroupRef.current.children.forEach((obj) => {
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) obj.material.dispose();
    });
    mapGroupRef.current.clear();
    if (map) drawRichMap(map, mapGroupRef.current, metersToUnits);
    renderOnce();
  }, [map, metersToUnits]);

  /* ---------- render current visible frame (vehicles + goals) ---------- */
  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return;

    const current = visibleFrames[frameIndex] || [];
    const wantIds = new Set(current.map(v => String(v.id)));

    // upsert vehicle meshes
    for (const v of current) {
      const idKey = String(v.id);
      if (!meshesRef.current.has(idKey)) {
        const geo = new THREE.BoxGeometry(4, 2, 1);
        const isEgo = String(v.id) === String(followRef.current);
        const mat = new THREE.MeshBasicMaterial({ color: isEgo ? 0xff3b30 : 0x2ecc71 });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(0, 0, 1.0);
        scene.add(mesh);
        meshesRef.current.set(idKey, { mesh, geo, mat });
      }
    }

    // remove stale vehicle meshes
    for (const [idKey, rec] of meshesRef.current.entries()) {
      if (!wantIds.has(idKey)) {
        scene.remove(rec.mesh);
        rec.geo.dispose();
        rec.mat.dispose();
        meshesRef.current.delete(idKey);
      }
    }

    // update transforms/colors
    for (const v of current) {
      const idKey = String(v.id);
      const rec = meshesRef.current.get(idKey);
      if (!rec) continue;
      const [x, y] = v.position;
      rec.mesh.position.set(x * metersToUnits, y * metersToUnits, 1.0);
      if (v.heading !== undefined) rec.mesh.rotation.z = v.heading;
      const isEgo = String(v.id) === String(followRef.current);
      rec.mat.color.setHex(isEgo ? 0xff3b30 : 0x2ecc71);
      
    }

    // --- GOALS (same logic as VehiclePlot) ---
    for (const v of current) {
      const idKey = String(v.id);
      const g = v.goal;
      const currentGoal = goalsRef.current.get(idKey);

      const hasRegion = Boolean(g?.region?.center);
      if (!hasRegion) {
        // remove if existed
        if (currentGoal?.rect) {
          scene.remove(currentGoal.rect.mesh);
          currentGoal.rect.geo.dispose();
          currentGoal.rect.mat.dispose();
        }
        goalsRef.current.delete(idKey);
        continue;
      }

      // normalize region
      const cx = Number(Array.isArray(g.region.center) ? g.region.center[0] : g.region.center?.[0]);
      const cy = Number(Array.isArray(g.region.center) ? g.region.center[1] : g.region.center?.[1]);
      const length = Number(g.region.length ?? 2.0);
      const width = Number(g.region.width ?? 3.5);
      const sigRect = `${cx},${cy},${length},${width},${metersToUnits}`;

      if (!currentGoal?.sigRect || currentGoal.sigRect !== sigRect) {
        if (currentGoal?.rect) {
          scene.remove(currentGoal.rect.mesh);
          currentGoal.rect.geo.dispose();
          currentGoal.rect.mat.dispose();
        }
        const rect = makeGoalRect([cx, cy], length, width, metersToUnits);
        scene.add(rect.mesh);
        goalsRef.current.set(idKey, { rect, sigRect });
      }
    }

    // remove goal visuals for vehicles not present this frame
    for (const [idKey, rec] of goalsRef.current.entries()) {
      if (!wantIds.has(idKey)) {
        if (rec.rect) {
          scene.remove(rec.rect.mesh);
          rec.rect.geo.dispose();
          rec.rect.mat.dispose();
        }
        goalsRef.current.delete(idKey);
      }
    }

    // follow camera
    if (followRef.current != null) {
      const rec = meshesRef.current.get(String(followRef.current));
      if (rec) {
        cameraRef.current.position.x = rec.mesh.position.x;
        cameraRef.current.position.y = rec.mesh.position.y;
        cameraRef.current.updateMatrixWorld();
      }
    }

    renderOnce();
  }, [frameIndex, visibleFrames, metersToUnits, followId]);

  const togglePlay = () => {
    setIsPlaying((p) => {
      const next = !p;
      isPlayingRef.current = next;
      onPlayStateChange?.(next);
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
          Frame {visibleFrames.length ? frameIndex + 1 : 0}/{visibleFrames.length || 0}
        </span>
        <span style={{ color: "#9aa0a6", fontSize: 12, marginLeft: 8 }}>
          (showing from index {effectiveStart})
        </span>
      </div>
    </div>
  );
}

/* ---------- keep GOAL in frames ---------- */
function normalizeFrames(input) {
  if (!input) return [];

  // Already list-of-lists
  if (Array.isArray(input) && Array.isArray(input[0])) return input;

  // Array of frame objects: [{ id: {position, heading, goal, ...}, ... }, ...]
  if (Array.isArray(input) && input.length && typeof input[0] === "object" && !Array.isArray(input[0])) {
    return input.map(frameObj =>
      Object.entries(frameObj).map(([id, v]) => ({
        id,
        position: v.position ?? [0, 0],
        heading: v.heading,
        color: v.is_human ? 0xff3b30 : 0x2ecc71,
        goal: v.goal, // <-- preserve goal
      }))
    );
  }

  // Single frame object
  if (typeof input === "object" && !Array.isArray(input)) {
    return [Object.entries(input).map(([id, v]) => ({
      id,
      position: v.position ?? [0, 0],
      heading: v.heading,
      color: v.is_human ? 0xff3b30 : 0x2ecc71,
      goal: v.goal, // <-- preserve goal
    }))];
  }

  return [];
}

/* ---------- map helper ---------- */
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

/* ---------- goal rectangle helper (same as VehiclePlot) ---------- */
function makeGoalRect(center, length, width, metersToUnits, color = 0x4caf50) {
  const [cx, cy] = center;
  const z = 0.06;

  const geo = new THREE.PlaneGeometry(length * metersToUnits, width * metersToUnits);
  const mat = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 0.6,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(cx * metersToUnits, cy * metersToUnits, z);
  return { mesh, geo, mat };
}
