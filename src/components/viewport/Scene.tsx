"use client"

import { useRef, useState, useCallback, useEffect } from "react"
import { Canvas } from "@react-three/fiber"
import { OrbitControls, Environment } from "@react-three/drei"
import { Suspense } from "react"
import * as THREE from "three"
import { ModelLoader } from "./ModelLoader"
import { DisplayModeApplier } from "./DisplayModes"
import { ClippingPlane } from "./ClippingPlane"
import type { DisplayMode, LightingPreset } from "./types"

function Grid() {
  const ref = useRef<THREE.GridHelper>(null!)
  useEffect(() => {
    ref.current = new THREE.GridHelper(20, 40, 0x374151, 0x374151)
  }, [])
  return <primitive object={ref.current} dispose={null} />
}

function LoadingFallback() {
  return (
    <mesh>
      <sphereGeometry args={[0.5, 16, 16]} />
      <meshNormalMaterial />
    </mesh>
  )
}

const LIGHTING_PRESETS: Record<string, string> = {
  none: "none",
  sunset: "sunset",
  dawn: "dawn",
  night: "night",
  warehouse: "warehouse",
  forest: "forest",
  apartment: "apartment",
  studio: "studio",
  city: "city",
  park: "park",
  lobby: "lobby",
}

export function CADViewport({
  modelUrl,
  displayMode = "shaded",
  lighting = "city",
  showGrid = true,
  showAxes = true,
  showStats = false,
  showEnvironment = true,
  enableClipping = false,
  overhangAngle = 45,
  clipNormal = [0, 1, 0] as [number, number, number],
  clipPosition = 0,
  autoRotate = false,
  enableDamping = true,
  onModelLoaded,
  onProgress,
  onError,
  onLoadStart,
}: {
  modelUrl?: string
  displayMode?: DisplayMode
  lighting?: LightingPreset
  showGrid?: boolean
  showAxes?: boolean
  showStats?: boolean
  showEnvironment?: boolean
  enableClipping?: boolean
  overhangAngle?: number
  clipNormal?: [number, number, number]
  clipPosition?: number
  autoRotate?: boolean
  enableDamping?: boolean
  onModelLoaded?: (object: THREE.Object3D) => void
  onProgress?: (progress: number) => void
  onError?: (error: string) => void
  onLoadStart?: () => void
}) {
  const groupRef = useRef<THREE.Group>(null!)
  const [loadedToken, setLoadedToken] = useState(0)
  const [modelLoaded, setModelLoaded] = useState(false)

  const environmentPreset = LIGHTING_PRESETS[lighting] || "city" as string

  const ext = modelUrl?.split(".").pop()?.toLowerCase()
  const isStep = ext === "step" || ext === "stp"

  const clipPlane = enableClipping
    ? new THREE.Plane(new THREE.Vector3(...clipNormal).normalize(), clipPosition)
    : null

  const handleModelLoaded = useCallback(
    (object: THREE.Object3D) => {
      setModelLoaded(true)
      setLoadedToken((t) => t + 1)
      onModelLoaded?.(object)
    },
    [onModelLoaded],
  )

  return (
    <div className="w-full h-full relative">
      <Canvas dpr={[1, 2]} shadows gl={{ preserveDrawingBuffer: true }}>
        <Suspense fallback={<LoadingFallback />}>
          {showGrid && <Grid />}
          {showEnvironment && lighting !== "none" && <Environment preset={environmentPreset as any} />}
          <ambientLight intensity={0.4} />
          <directionalLight position={[5, 10, 5]} intensity={1} castShadow />

          <ModelLoader
            ref={groupRef}
            modelUrl={isStep ? undefined : modelUrl}
            onLoaded={handleModelLoaded}
            onProgress={onProgress}
            onError={onError}
            onLoadStart={onLoadStart}
          />

          {modelLoaded && groupRef.current && (
            <DisplayModeApplier
              mode={displayMode}
              overhangAngle={overhangAngle}
              modelRef={groupRef}
              clipPlane={clipPlane}
              loadedToken={loadedToken}
            />
          )}

          {enableClipping && (
            <ClippingPlane
              normal={clipNormal}
              position={clipPosition}
              onChange={() => {}}
              visible={false}
            />
          )}

          <OrbitControls
            autoRotate={autoRotate}
            autoRotateSpeed={1}
            makeDefault
            minDistance={1}
            maxDistance={50}
          />
        </Suspense>
      </Canvas>

      {isStep && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="bg-yellow-900/80 text-yellow-100 px-4 py-2 rounded-lg text-sm backdrop-blur-sm">
            STEP files require conversion to GLTF/STL before rendering. Please
            upload a converted format.
          </div>
        </div>
      )}

      {!modelUrl && !isStep && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <p className="text-gray-500 text-lg font-medium select-none">
            No model loaded — send a prompt to generate
          </p>
        </div>
      )}
    </div>
  )
}
