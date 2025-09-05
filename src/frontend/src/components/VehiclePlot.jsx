import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export default function VehiclePlot({
  vehiclePos,
  heading,
  metersToUnits = 1,
  background = 0x0d0f13,
  trailLength = 200,
}) {
  const mountRef = useRef(null);

  // Three.js refs
  const rendererRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const vehicleRef = useRef(null);
  const frameRef = useRef(null);

  // Live data refs (updated by React effect, read in RAF loop)
  const posRef = useRef(vehiclePos);
  const headingRef = useRef(heading);

  useEffect(() => {
    posRef.current = vehiclePos;
    headingRef.current = heading;
  }, [vehiclePos, heading]);

  // Init once
  useEffect(() => {
    const mount = mountRef.current;
    const width = mount?.clientWidth || 600;
    const height = mount?.clientHeight || 400;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(background);

    // Camera (orthographic, top-down)
    const viewSize = 60; // world units visible vertically
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

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height);

    // Grid (XY plane)
    const grid = new THREE.GridHelper(400, 40, 0x555555, 0x2a2a2a);
    grid.rotation.x = Math.PI / 2; // default grid is XZ; rotate to XY
    scene.add(grid);

    // Axes helper (X=red, Y=green, Z=blue)
    const axes = new THREE.AxesHelper(20);
    scene.add(axes);

    // Vehicle mesh
    const carLength = 4;
    const carWidth = 2;
    const carThickness = 1;
    const vehicleGeo = new THREE.BoxGeometry(carLength, carWidth, carThickness);
    const vehicleMat = new THREE.MeshBasicMaterial({ color: 0xff3b30 });
    const vehicle = new THREE.Mesh(vehicleGeo, vehicleMat);
    vehicle.position.set(0, 0, 0.5);
    scene.add(vehicle);

    // Direction indicator
    const nose = new THREE.ArrowHelper(
      new THREE.Vector3(1, 0, 0),
      new THREE.Vector3(0, 0, 0.6),
      carLength * 0.75,
      0xffffff,
      0.8,
      0.4
    );
    vehicle.add(nose);

    // Trail
    const maxTrail = Math.max(10, trailLength);
    const trailPositions = new Float32Array(maxTrail * 3);
    const trailGeo = new THREE.BufferGeometry();
    trailGeo.setAttribute("position", new THREE.BufferAttribute(trailPositions, 3));
    const trailMat = new THREE.LineBasicMaterial({ transparent: true, opacity: 0.9 });
    const trail = new THREE.Line(trailGeo, trailMat);
    scene.add(trail);
    let trailCount = 0;

    // Mount
    if (mount) {
      mount.innerHTML = "";
      mount.appendChild(renderer.domElement);
    }

    // Resize
    const onResize = () => {
      const w = (mount && mount.clientWidth) || width;
      const h = (mount && mount.clientHeight) || height;
      const asp = w / h;
      camera.left = -viewSize * asp;
      camera.right = viewSize * asp;
      camera.top = viewSize;
      camera.bottom = -viewSize;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    // Animate
    const animate = () => {
      const [x, y] = posRef.current;
      const sx = x * metersToUnits;
      const sy = y * metersToUnits;

      vehicle.position.set(sx, sy, 0.5);
      if (headingRef.current !== undefined) {
        vehicle.rotation.z = headingRef.current;
      }

      // Trail (FIFO)
      if (trailCount < maxTrail) {
        trailPositions[trailCount * 3 + 0] = sx;
        trailPositions[trailCount * 3 + 1] = sy;
        trailPositions[trailCount * 3 + 2] = 0.4;
        trailCount++;
      } else {
        trailPositions.copyWithin(0, 3, maxTrail * 3);
        trailPositions[(maxTrail - 1) * 3 + 0] = sx;
        trailPositions[(maxTrail - 1) * 3 + 1] = sy;
        trailPositions[(maxTrail - 1) * 3 + 2] = 0.4;
      }
      trailGeo.setDrawRange(0, Math.min(trailCount, maxTrail));
      trailGeo.attributes.position.needsUpdate = true;

      renderer.render(scene, camera);
      frameRef.current = requestAnimationFrame(animate);
    };
    frameRef.current = requestAnimationFrame(animate);

    // Save refs
    sceneRef.current = scene;
    cameraRef.current = camera;
    rendererRef.current = renderer;
    vehicleRef.current = vehicle;

    // Cleanup
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      window.removeEventListener("resize", onResize);

      trailGeo.dispose();
      trailMat.dispose();
      vehicleGeo.dispose();
      vehicleMat.dispose();

      renderer.dispose();
      if (renderer.domElement && renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }

      scene.clear();
      sceneRef.current = null;
      cameraRef.current = null;
      rendererRef.current = null;
      vehicleRef.current = null;
    };
  }, [background, metersToUnits, trailLength]);

  // Optional: follow camera
  useEffect(() => {
    const camera = cameraRef.current;
    const vehicle = vehicleRef.current;
    if (!camera || !vehicle) return;

    const follow = false; // set true to follow
    if (!follow) return;

    const id = setInterval(() => {
      camera.position.x = vehicle.position.x;
      camera.position.y = vehicle.position.y;
      camera.updateMatrixWorld();
    }, 50);
    return () => clearInterval(id);
  }, []);

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
