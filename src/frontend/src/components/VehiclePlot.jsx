import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export default function VehiclePlot({
  vehicles = [],
  map = null,
  metersToUnits = 1,
  background = 0x0d0f13,
  followId = null,
}) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const frameRef = useRef(null);

  const meshesRef = useRef(new Map());
  const liveRef = useRef(new Map());
  const mapGroupRef = useRef(null);
  const followRef = useRef(followId);

  // keep the latest followId visible to the RAF loop
  useEffect(() => {
    followRef.current = followId;
  }, [followId]);

  // Keep live state fresh + upsert/remove meshes on vehicles change
  useEffect(() => {
    const next = new Map();
    for (const v of vehicles) next.set(v.id, { pos: v.pos, heading: v.heading, color: v.color });
    liveRef.current = next;

    const scene = sceneRef.current;
    if (!scene) return;

    const wantIds = new Set(vehicles.map(v => v.id));

    // upsert
    for (const v of vehicles) {
      if (!meshesRef.current.has(v.id)) {
        const geo = new THREE.BoxGeometry(4, 2, 1);
        const mat = new THREE.MeshBasicMaterial({ color: v.color ?? 0xff3b30 });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(0, 0, 1.0);
        scene.add(mesh);
        meshesRef.current.set(v.id, { mesh, geo, mat });
      } else if (v.color != null) {
        const rec = meshesRef.current.get(v.id);
        rec?.mat.color.setHex(v.color);
      }
    }

    // remove stale
    for (const [id, rec] of meshesRef.current.entries()) {
      if (!wantIds.has(id)) {
        scene.remove(rec.mesh);
        rec.geo.dispose();
        rec.mat.dispose();
        meshesRef.current.delete(id);
      }
    }
  }, [vehicles]);

  // Init once — IMPORTANT: do NOT depend on followId here
  useEffect(() => {
    const mount = mountRef.current;
    const width = mount?.clientWidth || 600;
    const height = mount?.clientHeight || 400;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(background);

    const aspect = width / height;
    const viewSize = 60;
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

    // grid
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

    // ⬅️ seed meshes for CURRENT vehicles so nothing disappears after a rebuild
    for (const v of vehicles) {
      if (!meshesRef.current.has(v.id)) {
        const geo = new THREE.BoxGeometry(4, 2, 1);
        const mat = new THREE.MeshBasicMaterial({ color: v.color ?? 0xff3b30 });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(0, 0, 1.0);
        scene.add(mesh);
        meshesRef.current.set(v.id, { mesh, geo, mat });
      }
    }

    // if map already present, draw it
    if (map) {
      drawRichMap(map, mapGroup, metersToUnits);
    }

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
    };
    window.addEventListener("resize", onResize);

    const animate = () => {
      for (const [id, state] of liveRef.current.entries()) {
        const rec = meshesRef.current.get(id);
        if (!rec) continue;
        const [x, y] = state.pos;
        rec.mesh.position.set(x * metersToUnits, y * metersToUnits, 1.0);
        if (state.heading !== undefined) rec.mesh.rotation.z = state.heading;
      }

      // follow handled every frame (no rebuild)
       const fid = followRef.current;
       if (fid && meshesRef.current.has(fid)) {
         const rec = meshesRef.current.get(fid);
         if (rec) {
           camera.position.x = rec.mesh.position.x;
           camera.position.y = rec.mesh.position.y;
           camera.updateMatrixWorld();
         }
      }

      renderer.render(scene, camera);
      frameRef.current = requestAnimationFrame(animate);
    };
    frameRef.current = requestAnimationFrame(animate);

    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      window.removeEventListener("resize", onResize);

      for (const [, rec] of meshesRef.current.entries()) {
        scene.remove(rec.mesh);
        rec.geo.dispose();
        rec.mat.dispose();
      }
      meshesRef.current.clear();

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
  }, [background, metersToUnits]); // <- followId REMOVED here

  // Draw the map (or redraw on scale change)
  useEffect(() => {
    if (!map || !mapGroupRef.current) return;
    // clear and redraw
    mapGroupRef.current.children.forEach((obj) => {
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) obj.material.dispose();
    });
    mapGroupRef.current.clear();
    drawRichMap(map, mapGroupRef.current, metersToUnits);
  }, [map, metersToUnits]);

  return (
    <div
      ref={mountRef}
      style={{ width: "100%", height: 400, borderRadius: 12, overflow: "hidden", background: "#0d0f13" }}
    />
  );
}

// --- same drawRichMap helper you already have ---
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
      const mat = new THREE.LineBasicMaterial({ color: defaultLaneColor, transparent: true, opacity: 0.7, depthWrite: false });
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
      const mat = new THREE.LineDashedMaterial({ color, transparent: true, opacity: 0.95, dashSize, gapSize, depthWrite: false });
      const line = new THREE.Line(geo, mat);
      line.computeLineDistances();
      line.renderOrder = 2;
      group.add(line);
    } else {
      const mat = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.95, depthWrite: false });
      const line = new THREE.Line(geo, mat);
      line.renderOrder = 2;
      group.add(line);
    }
  }
}
