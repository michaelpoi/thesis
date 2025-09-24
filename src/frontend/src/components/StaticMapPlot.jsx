import React, { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * StaticMapPlot — draws only the map and fits/centers it in view.
 *
 * Props:
 *  - map: {
 *      features?: Array<{
 *        kind: "lane" | "road_line" | "boundary_line",
 *        polyline: [number, number][],
 *        style?: { color?: string, pattern?: "solid" | "dashed" }
 *      }>
 *    } | null
 *  - metersToUnits?: number
 *  - background?: number
 *  - showGrid?: boolean
 */
export default function StaticMapPlot({
  map = null,
  metersToUnits = 1,
  background = 0x0d0f13,
  showGrid = true,
}) {
  const mountRef = useRef(null);

  // three.js singletons
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);

  // groups
  const mapGroupRef = useRef(null);

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

    // save
    sceneRef.current = scene;
    cameraRef.current = camera;
    rendererRef.current = renderer;
    mapGroupRef.current = mapGroup;

    // resize: re-fit to map and re-render
    const onResize = () => {
      if (!mount || !cameraRef.current || !rendererRef.current) return;
      const w = mount.clientWidth || width;
      const h = mount.clientHeight || height;
      rendererRef.current.setSize(w, h);
      fitCameraToMap(map, metersToUnits);
      renderOnce();
    };
    window.addEventListener("resize", onResize);

    // initial render
    renderFrame();

    return () => {
      window.removeEventListener("resize", onResize);
      if (mapGroup) disposeGroup(mapGroup);
      renderer.dispose();
      if (renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
      sceneRef.current = null;
      cameraRef.current = null;
      rendererRef.current = null;
      mapGroupRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [background, showGrid]);

  // (re)draw map whenever inputs change
  useEffect(() => {
    renderFrame();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, metersToUnits]);

  const renderFrame = () => {
    if (!sceneRef.current || !rendererRef.current || !cameraRef.current) return;

    if (mapGroupRef.current) {
      disposeGroup(mapGroupRef.current);
      mapGroupRef.current.clear();
      if (map) drawRichMap(map, mapGroupRef.current, metersToUnits);
    }

    // Center & fit camera to current map
    fitCameraToMap(map, metersToUnits);

    renderOnce();
  };

  const renderOnce = () => {
    if (!sceneRef.current || !rendererRef.current || !cameraRef.current) return;
    rendererRef.current.render(sceneRef.current, cameraRef.current);
  };

  /** Fit the orthographic camera to encompass the map bounds with padding */
  const fitCameraToMap = (mapObj, mtu, paddingFactor = 1.15) => {
    const camera = cameraRef.current;
    const mount = mountRef.current;
    if (!camera || !mount || !mapObj?.features?.length) return;

    // compute bounds
    const bbox = new THREE.Box2();
    let hasPoint = false;
    for (const f of mapObj.features) {
      const poly = f.polyline || [];
      for (const [x, y] of poly) {
        const vx = x * mtu;
        const vy = y * mtu;
        if (!hasPoint) {
          bbox.min.set(vx, vy);
          bbox.max.set(vx, vy);
          hasPoint = true;
        } else {
          bbox.expandByPoint(new THREE.Vector2(vx, vy));
        }
      }
    }
    if (!hasPoint) return;

    const width = mount.clientWidth || 600;
    const height = mount.clientHeight || 400;
    const aspect = width / height;

    const spanX = Math.max(1e-6, bbox.max.x - bbox.min.x);
    const spanY = Math.max(1e-6, bbox.max.y - bbox.min.y);

    const cx = (bbox.min.x + bbox.max.x) / 2;
    const cy = (bbox.min.y + bbox.max.y) / 2;

    // compute viewSizeY to fit both X/Y spans with padding
    let viewSizeY = (spanY / 2) * paddingFactor;
    const viewSizeX = ((spanX / 2) * paddingFactor) / aspect;
    if (viewSizeX > viewSizeY) viewSizeY = viewSizeX;

    camera.left = -viewSizeY * aspect;
    camera.right = viewSizeY * aspect;
    camera.top = viewSizeY;
    camera.bottom = -viewSizeY;
    camera.updateProjectionMatrix();

    camera.position.set(cx, cy, 100);
    camera.lookAt(cx, cy, 0);
    camera.updateMatrixWorld();
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
    if (obj.material) {
      if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose());
      else obj.material.dispose();
    }
  }
}

function drawRichMap(mapObj, group, metersToUnits) {
  const features = mapObj?.features || [];
  const defaultLaneColor = 0x9aa0a6; // neutral lane hint

  for (const f of features) {
    const pts = (f.polyline || []).map(
      ([x, y]) => new THREE.Vector3(x * metersToUnits, y * metersToUnits, 0.02)
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
