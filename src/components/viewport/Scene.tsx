"use client"

import { Canvas, useLoader } from "@react-three/fiber"
import { OrbitControls, Grid, Environment, ContactShadows } from "@react-three/drei"
import { Suspense, useEffect } from "react"
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader"
import { STLLoader } from "three/examples/jsm/loaders/STLLoader"
import * as THREE from "three"

function SceneModel({ url, wireframe }: { url: string; wireframe?: boolean }) {
  const ext = url.split(".").pop()?.toLowerCase()

  if (ext === "gltf" || ext === "glb") {
    const gltf = useLoader(GLTFLoader, url)
    useEffect(() => {
      gltf.scene.traverse((child: any) => {
        if (child.isMesh) {
          child.castShadow = true
          child.receiveShadow = true
          if (wireframe) {
            child.material = new THREE.MeshBasicMaterial({ color: 0x3b82f6, wireframe: true })
          }
        }
      })
    }, [gltf, wireframe])
    return <primitive object={gltf.scene} />
  }

  if (ext === "stl") {
    const geometry = useLoader(STLLoader, url)
    return (
      <mesh geometry={geometry} rotation={[-Math.PI / 2, 0, 0]} castShadow receiveShadow wireframe={wireframe}>
        <meshStandardMaterial color="#6b7280" metalness={0.3} roughness={0.6} />
      </mesh>
    )
  }

  return null
}

function SceneContent({ modelUrl, wireframe }: { modelUrl: string; wireframe?: boolean }) {
  return (
    <>
      <Grid args={[20, 20]} cellSize={0.5} cellThickness={0.5} cellColor="#374151" sectionSize={2} sectionThickness={1} sectionColor="#4b5563" fadeDistance={30} />
      <Environment preset="city" />
      <ContactShadows position={[0, -0.01, 0]} opacity={0.4} scale={20} blur={2} far={4} color="#1f2937" />
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 10, 5]} intensity={1} castShadow />
      {modelUrl && <SceneModel url={modelUrl} wireframe={wireframe} />}
    </>
  )
}

function LoadingFallback() {
  return (
    <mesh>
      <sphereGeometry args={[0.5, 16, 16]} />
      <meshNormalMaterial />
    </mesh>
  )
}

export function CADViewport({
  modelUrl,
  wireframe,
  autoRotate,
  displayMode,
  lighting,
  showGrid,
  showAxes,
  showStats,
  showEnvironment,
  enableClipping,
  enableDamping,
}: {
  modelUrl?: string
  wireframe?: boolean
  autoRotate?: boolean
  displayMode?: string
  lighting?: string
  showGrid?: boolean
  showAxes?: boolean
  showStats?: boolean
  showEnvironment?: boolean
  enableClipping?: boolean
  enableDamping?: boolean
}) {
  const ext = modelUrl?.split(".").pop()?.toLowerCase()
  const isStep = ext === "step" || ext === "stp"

  return (
    <div className="w-full h-full relative">
      <Canvas dpr={[1, 2]} shadows gl={{ preserveDrawingBuffer: true }}>
        <Suspense fallback={<LoadingFallback />}>
          <SceneContent modelUrl={isStep ? "" : (modelUrl || "")} wireframe={wireframe} />
          <OrbitControls autoRotate={autoRotate} autoRotateSpeed={1} makeDefault minDistance={1} maxDistance={50} />
        </Suspense>
      </Canvas>

      {isStep && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="bg-yellow-900/80 text-yellow-100 px-4 py-2 rounded-lg text-sm backdrop-blur-sm">
            STEP files require conversion to GLTF/STL before rendering. Please upload a converted format.
          </div>
        </div>
      )}

      {!modelUrl && !isStep && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <p className="text-gray-500 text-lg font-medium select-none">No model loaded — send a prompt to generate</p>
        </div>
      )}
    </div>
  )
}
