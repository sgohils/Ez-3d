"use client"

import { useMemo, useRef, useState, type ReactNode } from "react"
import * as THREE from "three"
import { Canvas } from "@react-three/fiber"
import { OrbitControls, Environment, Stats, Html } from "@react-three/drei"
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib"
import { ModelLoader } from "./ModelLoader"
import { DisplayModeApplier, DisplayModes } from "./DisplayModes"
import { ClippingPlane } from "./ClippingPlane"
import type { CADViewportProps, DisplayMode, LightingPreset } from "./types"

function ViewportGrid({
  size = 200,
  divisions = 40,
  visible = true,
}: {
  size?: number
  divisions?: number
  visible?: boolean
}) {
  const helper = useMemo(
    () => new THREE.GridHelper(size, divisions, 0x6b7280, 0x1f2937),
    [size, divisions],
  )
  if (!visible) return null
  return <primitive object={helper} />
}
ViewportGrid.displayName = "ViewportGrid"

function ViewportAxes({ size = 100, visible = true }: { size?: number; visible?: boolean }) {
  const helper = useMemo(() => new THREE.AxesHelper(size), [size])
  if (!visible) return null
  return <primitive object={helper} />
}
ViewportAxes.displayName = "ViewportAxes"

interface ViewportSceneProps {
  lighting: LightingPreset
  showGrid: boolean
  showAxes: boolean
  showStats: boolean
  showEnvironment: boolean
  enableDamping: boolean
  autoRotate: boolean
  controlsRef: React.RefObject<OrbitControlsImpl>
  children?: ReactNode
}

export function ViewportScene({
  lighting,
  showGrid,
  showAxes,
  showStats,
  showEnvironment,
  enableDamping,
  autoRotate,
  controlsRef,
  children,
}: ViewportSceneProps) {
  return (
    <>
      <color attach="background" args={["#0f1117"]} />

      {showEnvironment && lighting !== "none" ? (
        <Environment preset={lighting} background={false} />
      ) : (
        <>
          <ambientLight intensity={0.4} />
          <directionalLight
            position={[10, 20, 10]}
            intensity={1.2}
            castShadow
            shadow-camera-far={200}
            shadow-camera-left={-50}
            shadow-camera-right={50}
            shadow-camera-top={50}
            shadow-camera-bottom={-50}
            shadow-map-size-width={1024}
            shadow-map-size-height={1024}
          />
        </>
      )}

      <OrbitControls
        ref={controlsRef}
        enableDamping={enableDamping}
        autoRotate={autoRotate}
        enablePan
        enableZoom
        enableRotate
        makeDefault
      />

      <ViewportGrid visible={showGrid} />
      <ViewportAxes visible={showAxes} />

      {children}
      {showStats && <Stats />}
    </>
  )
}
ViewportScene.displayName = "ViewportScene"

function fitCameraTo(controls: OrbitControlsImpl | null, object: THREE.Object3D) {
  if (!controls) return
  const camera = controls.object
  const box = new THREE.Box3().setFromObject(object)
  if (box.isEmpty()) return
  const size = new THREE.Vector3()
  box.getSize(size)
  const center = new THREE.Vector3()
  box.getCenter(center)

  controls.target.copy(center)
  const distance = Math.max(size.length(), 10) * 1.5
  camera.position
    .copy(center)
    .add(new THREE.Vector3(0, 0, 1).multiplyScalar(distance))
    .add(new THREE.Vector3(0, distance * 0.3, 0))
  camera.near = Math.min(camera.near, Math.max(size.length() * 0.01, 0.1))
  camera.far = Math.max(camera.far, size.length() * 4)
  camera.updateProjectionMatrix()
  controls.update()
}

export function CADViewport({
  modelUrl,
  model,
  displayMode = "shaded",
  lighting = "warehouse",
  showGrid = true,
  showAxes = true,
  showStats = false,
  showEnvironment = true,
  enableClipping = false,
  overhangAngle = 45,
  clipNormal = [0, 0, 1],
  clipPosition = 0,
  autoRotate = false,
  enableDamping = true,
  onModelLoaded,
  onProgress,
  onError,
  onLoadStart,
  className,
  children,
}: CADViewportProps) {
  const [mode, setMode] = useState<DisplayMode>(displayMode)
  const [overhangAngleState, setOverhangAngleState] = useState(overhangAngle)
  const [clippingEnabled, setClippingEnabled] = useState(enableClipping)
  const [clipNormalState, setClipNormalState] =
    useState<[number, number, number]>(clipNormal)
  const [clipPositionState, setClipPositionState] = useState(clipPosition)
  const [error, setError] = useState<string | null>(null)
  const [loadedToken, setLoadedToken] = useState(0)

  const controlsRef = useRef<OrbitControlsImpl>(null!)
  const modelRef = useRef<THREE.Group>(null!)

  const handleModelLoaded = (object: THREE.Object3D) => {
    onModelLoaded?.(object)
    fitCameraTo(controlsRef.current, object)
    setLoadedToken((t) => t + 1)
  }

  const clippingPlane = useMemo(
    () =>
      clippingEnabled
        ? new THREE.Plane(
            new THREE.Vector3(...clipNormalState).normalize(),
            clipPositionState,
          )
        : null,
    [clippingEnabled, clipNormalState, clipPositionState],
  )

  return (
    <div className="relative flex h-full w-full flex-col">
      <Canvas
        camera={{ position: [0, 0, 60], fov: 50, near: 0.1, far: 2000 }}
        gl={{ antialias: true, preserveDrawingBuffer: true, stencil: true }}
        className={className}
      >
        <ViewportScene
          lighting={lighting}
          showGrid={showGrid}
          showAxes={showAxes}
          showStats={showStats}
          showEnvironment={showEnvironment}
          enableDamping={enableDamping}
          autoRotate={autoRotate}
          controlsRef={controlsRef}
        >
        {modelUrl || model ? (
          <ModelLoader
            ref={modelRef}
            modelUrl={modelUrl}
            model={model}
            onLoaded={handleModelLoaded}
            onProgress={onProgress}
            onError={(err) => {
              setError(err)
              onError?.(err)
            }}
            onLoadStart={onLoadStart}
          />
        ) : null}
        </ViewportScene>

        {!modelUrl && !model ? (
          <Html
            center
            style={{
              color: "#9ca3af",
              font: '13px/1.5 ui-sans, system-ui',
              pointerEvents: "none",
            }}
          >
            No model loaded. Send a prompt to generate a 3D model.
          </Html>
        ) : null}

        <DisplayModeApplier
          mode={mode}
          overhangAngle={overhangAngleState}
          modelRef={modelRef}
          clipPlane={clippingPlane}
          loadedToken={loadedToken}
        />

        {clippingEnabled && clippingPlane ? (
          <ClippingPlane
            normal={clipNormalState}
            position={clipPositionState}
            onChange={setClipPositionState}
            visible={true}
          />
        ) : null}

        {children}
      </Canvas>

      <div className="pointer-events-auto absolute top-4 left-4 z-10">
        <DisplayModes
          mode={mode}
          onModeChange={setMode}
          overhangAngle={overhangAngleState}
          onOverhangAngleChange={setOverhangAngleState}
          clippingEnabled={clippingEnabled}
          onClippingChange={setClippingEnabled}
          clipPosition={clipPositionState}
          onClipPositionChange={setClipPositionState}
          clipNormal={clipNormalState}
          onClipNormalChange={setClipNormalState}
        />
      </div>

      {error ? (
        <div
          className="pointer-events-auto absolute bottom-4 left-1/2 -translate-x-1/2 z-10 rounded-lg
            bg-red-500/10 border border-red-500/30 px-3 py-2 text-sm text-red-300"
        >
          {error}
        </div>
      ) : null}
    </div>
  )
}
CADViewport.displayName = "CADViewport"
