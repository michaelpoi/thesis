import React, { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * StaticVehiclePlot — renders a single snapshot (no RAF loop).
 *
 * Props:
 *  vehicles: Array<{ id: string, pos: [number, number], heading?: number, color?: number }>
 *  map: {
 *    lane_width?: number,
 *    features?: Array<{
 *      kind: "lane" | "road_line" | "boundary_line",
 *      polyline: [number, number][],
 *      style?: {
 *        width?: number,               // for lanes
 *        color?: string,               // "#FFFFFF" | "#FFD400"
 *        pattern?: "solid" | "dashed", // for lines
 *        line_width?: number
 *      }
 *    }>
 *  } | null
 *  metersToUnits?: number
 *  background?: number
 *  followId?: string | null           // center camera on this vehicle once
 *  showGrid?: boolean                 // default true
 *
 *  // NEW: optional trajectory as list-of-lists (e.g., [[x,y],[x,y],...])
 *  trajectory?: [number, number][] | null
 *  trajectoryColor?: string | number  // default "#00E5FF"
 *  trajectoryWidth?: number           // default 2.0 (in line units)
 *  trajectoryDashed?: boolean         // default false
 */
export default function StaticVehiclePlot({
  vehicles = [],
  map = null,
  metersToUnits = 1,
  background = 0x0d0f13,
  followId = null,
  showGrid = true,
  trajectory = null,
  trajectoryColor = "#00E5FF",
  trajectoryWidth = 2.0,
  trajectoryDashed = false,
}) {
  const mountRef = useRef(null);

  // three.js singletons
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);

  // groups
  const mapGroupRef = useRef(null);
  const vehiclesGroupRef = useRef(null);
  const trajGroupRef = useRef(null);

  // init once
  useEffect(() => {
    const mount = mountRef.current;
    const width = mount?.clientWidth || 600;
    const height = mount?.clientHeight || 400;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(background);

    const aspect = width / height;
    const viewSize = 60;
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

    // mount
    mount.innerHTML = "";
    mount.appendChild(renderer.domElement);

    // optional grid
    if (showGrid) {
      const grid = new THREE.GridHelper(400, 40, 0x444444, 0x222222);
      grid.rotation.x = Math.PI / 2;
      grid.renderOrder = 0;
      scene.add(grid);
    }

    // groups
    const mapGroup = new THREE.Group();
    mapGroup.renderOrder = 1;
    scene.add(mapGroup);

    const trajGroup = new THREE.Group();
    trajGroup.renderOrder = 2;
    scene.add(trajGroup);

    const vehiclesGroup = new THREE.Group();
    vehiclesGroup.renderOrder = 3;
    scene.add(vehiclesGroup);

    // save
    sceneRef.current = scene;
    cameraRef.current = camera;
    rendererRef.current = renderer;
    mapGroupRef.current = mapGroup;
    trajGroupRef.current = trajGroup;
    vehiclesGroupRef.current = vehiclesGroup;

    // resize: recompute frustum and re-render once
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
      // re-render current frame
      renderOnce();
    };
    window.addEventListener("resize", onResize);

    // initial render
    renderOnce();

    return () => {
      window.removeEventListener("resize", onResize);

      // dispose groups
      disposeGroup(mapGroup);
      disposeGroup(trajGroup);
      disposeGroup(vehiclesGroup);

      // dispose renderer
      renderer.dispose();
      if (renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }

      // clear refs
      sceneRef.current = null;
      cameraRef.current = null;
      rendererRef.current = null;
      mapGroupRef.current = null;
      trajGroupRef.current = null;
      vehiclesGroupRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [background, showGrid]); // init only on fundamentals

  // (re)draw whenever inputs change
  useEffect(() => {
    if (!sceneRef.current || !rendererRef.current || !cameraRef.current) return;

    // redraw map
    if (mapGroupRef.current) {
      disposeGroup(mapGroupRef.current);
      mapGroupRef.current.clear();
      if (map) drawRichMap(map, mapGroupRef.current, metersToUnits);
    }

    // redraw trajectory (optional)
    if (trajGroupRef.current) {
      disposeGroup(trajGroupRef.current);
      trajGroupRef.current.clear();
      if (trajectory && trajectory.length >= 2) {
        drawTrajectory(
          trajectory,
          trajGroupRef.current,
          metersToUnits,
          trajectoryColor,
          trajectoryWidth,
          trajectoryDashed
        );
      }
    }

    // redraw vehicles
    if (vehiclesGroupRef.current) {
      disposeGroup(vehiclesGroupRef.current);
      vehiclesGroupRef.current.clear();
      drawVehicles(vehicles, vehiclesGroupRef.current, metersToUnits);
    }

    // follow once (center camera on followId)
    if (followId) {
      const found = vehicles.find((v) => v.id === followId);
      if (found) {
        const [x, y] = found.pos;
        cameraRef.current.position.x = x * metersToUnits;
        cameraRef.current.position.y = y * metersToUnits;
        cameraRef.current.updateMatrixWorld();
      }
    }

    renderOnce();
  }, [
    vehicles,
    map,
    metersToUnits,
    followId,
    trajectory,
    trajectoryColor,
    trajectoryWidth,
    trajectoryDashed,
  ]);

  const renderOnce = () => {
    if (!sceneRef.current || !rendererRef.current || !cameraRef.current) return;
    rendererRef.current.render(sceneRef.current, cameraRef.current);
  };

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

/* ---------- helpers ---------- */

function disposeGroup(group) {
  for (const obj of group.children) {
    if (obj.geometry) obj.geometry.dispose();
    if (obj.material) obj.material.dispose();
  }
}

function drawVehicles(vehicles, group, metersToUnits) {
  for (const v of vehicles) {
    const geo = new THREE.BoxGeometry(4, 2, 1);
    const mat = new THREE.MeshBasicMaterial({ color: v.color ?? 0xff3b30 });
    const mesh = new THREE.Mesh(geo, mat);
    const [x, y] = v.pos;
    mesh.position.set(x * metersToUnits, y * metersToUnits, 1.0);
    if (v.heading !== undefined) mesh.rotation.z = v.heading;
    group.add(mesh);
  }
}

function drawRichMap(mapObj, group, metersToUnits) {
  const features = mapObj?.features || [];
  const defaultLaneColor = 0x9aa0a6; // neutral lane hint

  for (const f of features) {
    const pts = (f.polyline || []).map(([x, y]) =>
      new THREE.Vector3(x * metersToUnits, y * metersToUnits, 0.02)
    );
    if (pts.length < 2) continue;

    const geo = new THREE.BufferGeometry().setFromPoints(pts);

    if (f.kind === "lane") {
      // Thin neutral line; later you can extrude by width if desired
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

    // road_line / boundary_line
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
      line.computeLineDistances(); // required for dashes
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

function drawTrajectory(
  points,                // [[x,y], [x,y], ...]
  group,
  metersToUnits,
  color = "#00E5FF",
  width = 2.0,
  dashed = false
) {
  const pts = points.map(([x, y]) => new THREE.Vector3(
    x * metersToUnits,
    y * metersToUnits,
    0.5   // slightly above map lines
  ));
  if (pts.length < 2) return;

  const geo = new THREE.BufferGeometry().setFromPoints(pts);

  if (dashed) {
    const mat = new THREE.LineDashedMaterial({
      color: new THREE.Color(color),
      linewidth: width,      // note: ignored in most WebGL contexts, kept for completeness
      dashSize: 1.0 * metersToUnits,
      gapSize: 0.8 * metersToUnits,
      transparent: true,
      opacity: 0.95,
      depthWrite: false,
    });
    const line = new THREE.Line(geo, mat);
    line.computeLineDistances();
    line.renderOrder = 3;
    group.add(line);
  } else {
    const mat = new THREE.LineBasicMaterial({
      color: new THREE.Color(color),
      linewidth: width,      // note: ignored in most WebGL contexts
      transparent: true,
      opacity: 0.95,
      depthWrite: false,
    });
    const line = new THREE.Line(geo, mat);
    line.renderOrder = 3;
    group.add(line);
  }
}
