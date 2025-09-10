import React, { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * Props:
 *  vehicles: Array<{ id: string, pos: [number, number], heading?: number, color?: number }>
 *  map: { [laneId]: { x: number[], y: number[] } } | null
 *  metersToUnits?: number
 *  background?: number
 *  followId?: string | null
 */
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

  const meshesRef = useRef(new Map()); // id -> { mesh, geo, mat }
  const liveRef = useRef(new Map());   // id -> { pos, heading, color }
  const mapGroupRef = useRef(null);    // THREE.Group for all lane lines

  // Keep vehicle state fresh and upsert/remove meshes
  useEffect(() => {
    const next = new Map();
    for (const v of vehicles) next.set(v.id, { pos: v.pos, heading: v.heading, color: v.color });
    liveRef.current = next;

    const scene = sceneRef.current;
    if (!scene) return;

    const wantIds = new Set(vehicles.map(v => v.id));

    // upsert vehicles
    for (const v of vehicles) {
      if (!meshesRef.current.has(v.id)) {
        const geo = new THREE.BoxGeometry(4, 2, 1);
        const mat = new THREE.MeshBasicMaterial({ color: v.color ?? 0xff3b30 });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(0, 0, 1.0); // slightly above map lines/grid
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

  // Init three.js once (IMPORTANT: do NOT depend on `map` here)
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

    // Optional grid
    const grid = new THREE.GridHelper(400, 40, 0x444444, 0x222222);
    grid.rotation.x = Math.PI / 2;
    // Keep grid from occluding
    grid.renderOrder = 0;
    scene.add(grid);

    // Group to hold map lines
    const mapGroup = new THREE.Group();
    mapGroup.renderOrder = 1;
    scene.add(mapGroup);

    sceneRef.current = scene;
    cameraRef.current = camera;
    rendererRef.current = renderer;
    mapGroupRef.current = mapGroup;

    // Resize handling
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

    // Animation loop
    const animate = () => {
      for (const [id, state] of liveRef.current.entries()) {
        const rec = meshesRef.current.get(id);
        if (!rec) continue;
        const [x, y] = state.pos;
        rec.mesh.position.set(x * metersToUnits, y * metersToUnits, 1.0);
        if (state.heading !== undefined) rec.mesh.rotation.z = state.heading;
      }

      // Camera follow
      if (followId && meshesRef.current.has(followId)) {
        const rec = meshesRef.current.get(followId);
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

    // Cleanup
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      window.removeEventListener("resize", onResize);

      // Dispose vehicle meshes
      for (const [, rec] of meshesRef.current.entries()) {
        scene.remove(rec.mesh);
        rec.geo.dispose();
        rec.mat.dispose();
      }
      meshesRef.current.clear();

      // Dispose map lines
      if (mapGroupRef.current) {
        mapGroupRef.current.children.forEach((obj) => {
          const line = obj; // THREE.Line
          if (line.geometry) line.geometry.dispose();
          if (line.material) line.material.dispose();
        });
        scene.remove(mapGroupRef.current);
        mapGroupRef.current = null;
      }

      renderer.dispose();
      if (renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
    };
  }, [background, metersToUnits, followId]); // <- removed `map`

  // Draw the map once (or when metersToUnits changes)
  useEffect(() => {
    if (!map || !mapGroupRef.current) return;
    // Clear any previous lines if you want to redraw on scale change
    mapGroupRef.current.children.forEach((obj) => {
      const line = obj;
      if (line.geometry) line.geometry.dispose();
      if (line.material) line.material.dispose();
    });
    mapGroupRef.current.clear();

    drawMap(map, mapGroupRef.current, metersToUnits);
  }, [map, metersToUnits]);

  return (
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
  );
}

// --- helpers ---
function drawMap(mapObj, group, metersToUnits) {
  // mapObj: { [laneId]: { x: number[], y: number[] } }
  for (const lane of Object.values(mapObj)) {
    const pts = lane.x.map((x, i) =>
      new THREE.Vector3(x * metersToUnits, lane.y[i] * metersToUnits, 0.01)
    );
    const geo = new THREE.BufferGeometry().setFromPoints(pts);
    const mat = new THREE.LineBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.9,
      depthWrite: false, // <- keep lines from occluding cars
      // depthTest: false, // (optional) if you still see flicker/occlusion
    });
    const line = new THREE.Line(geo, mat);
    line.renderOrder = 1; // render before vehicles (vehicles set z=1 anyway)
    group.add(line);
  }
}
