"use client"

import React, {
  ReactNode,
  Suspense,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  forwardRef,
} from "react"
import * as THREE from "three"
import { Html, useGLTF, useProgress } from "@react-three/drei"
import { useLoader } from "@react-three/fiber"
import { STLLoader } from "three/examples/jsm/loaders/STLLoader"

export type LoadedObject = THREE.Object3D

function getBaseName(url: string): string {
  return url.split("#")[0].split("?")[0].toLowerCase()
}

function isStlUrl(url: string): boolean {
  return getBaseName(url).endsWith(".stl")
}

interface ModelContentProps {
  modelUrl?: string
  model?: THREE.Object3D
  onError?: (error: string) => void
  onLoaded?: (object: THREE.Object3D) => void
}

interface UrlContentProps {
  modelUrl: string
  onLoaded?: (object: THREE.Object3D) => void
}

const STLContent: React.FC<UrlContentProps> = ({ modelUrl, onLoaded }) => {
  const geometry = useLoader(STLLoader, modelUrl)
  const meshRef = useRef<THREE.Mesh>(null!)

  useEffect(() => {
    if (meshRef.current) onLoaded?.(meshRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [geometry, onLoaded])

  return (
    <mesh ref={meshRef} geometry={geometry}>
      <meshStandardMaterial color="#c9b1ff" />
    </mesh>
  )
}

const GLTFContent: React.FC<UrlContentProps> = ({ modelUrl, onLoaded }) => {
  const gltf = useGLTF(modelUrl)
  useEffect(() => {
    onLoaded?.(gltf.scene)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gltf, onLoaded])
  return <primitive object={gltf.scene} />
}

const InlineModelContent: React.FC<ModelContentProps> = ({ model, onLoaded }) => {
  const object = useMemo(() => model?.clone(), [model])
  useEffect(() => {
    if (object) onLoaded?.(object)
  }, [object, onLoaded])
  if (!object) return null
  return <primitive object={object} />
}

function ModelContent({ modelUrl, model, onLoaded }: ModelContentProps) {
  if (model) return <InlineModelContent model={model} onLoaded={onLoaded} />
  if (modelUrl) {
    if (isStlUrl(modelUrl)) {
      return <STLContent modelUrl={modelUrl} onLoaded={onLoaded} />
    }
    return <GLTFContent modelUrl={modelUrl} onLoaded={onLoaded} />
  }
  return null
}

const ProgressOverlay: React.FC<{ onProgress?: (progress: number) => void }> = ({
  onProgress,
}) => {
  const { progress, active, errors } = useProgress()
  useEffect(() => {
    onProgress?.(progress)
  }, [progress, onProgress])

  if (!active && progress >= 100) return null
  return (
    <Html
      center
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "6px",
        color: "#e5e7eb",
        font: '12px/1.5 ui-monospace, "Segoe UI", Roboto, monospace',
        pointerEvents: "none",
      }}
    >
      <span>Loading model… {Math.round(progress)}%</span>
      {errors.length > 0 && (
        <span style={{ color: "#fca5a5" }}>{errors[errors.length - 1]}</span>
      )}
    </Html>
  )
}

interface ErrorBoundaryProps {
  fallback?: ReactNode
  children?: ReactNode
  onError?: (error: Error) => void
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  override state: ErrorBoundaryState = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  override componentDidCatch(error: Error) {
    this.props.onError?.(error)
  }

  retry = () => this.setState({ hasError: false, error: null })

  override render() {
    if (this.state.hasError) {
      const message = this.state.error?.message ?? "Failed to load model"
      return (
        this.props.fallback ?? (
          <Html center>
            <div
              style={{
                padding: "16px 20px",
                background: "#1f2937",
                border: "1px solid #ef4444",
                borderRadius: "8px",
                color: "#fca5a5",
                font: '12px/1.4 ui-monospace, "Segoe UI", Roboto, monospace',
                display: "flex",
                flexDirection: "column",
                gap: "8px",
                pointerEvents: "auto",
              }}
            >
              <span>Model load error</span>
              <code style={{ color: "#fecaca", wordBreak: "break-word" }}>{message}</code>
              <button
                onClick={this.retry}
                style={{
                  padding: "4px 10px",
                  fontSize: "12px",
                  background: "#2563eb",
                  color: "#fff",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Retry
              </button>
            </div>
          </Html>
        )
      )
    }
    return this.props.children
  }
}

export interface ModelLoaderProps {
  modelUrl?: string
  model?: THREE.Object3D
  onLoaded?: (object: THREE.Object3D) => void
  onProgress?: (progress: number) => void
  onError?: (error: string) => void
  onLoadStart?: () => void
}

export const ModelLoader = forwardRef<THREE.Group, ModelLoaderProps>(
  (
    { modelUrl, model, onLoaded, onProgress, onError, onLoadStart },
    ref,
  ) => {
    const groupRef = useRef<THREE.Group>(null!)
    useImperativeHandle(ref, () => groupRef.current)

    useEffect(() => {
      onLoadStart?.()
    }, [onLoadStart])

    const key = modelUrl ?? (model ? model.uuid : "empty")

    const boundaryOnError = (error: Error) => {
      onError?.(error.message)
    }

    return (
      <group ref={groupRef} key={key}>
        <ErrorBoundary onError={boundaryOnError}>
          <Suspense
            fallback={<ProgressOverlay onProgress={onProgress} />}
          >
            <ModelContent
              modelUrl={modelUrl}
              model={model}
              onLoaded={onLoaded}
            />
          </Suspense>
        </ErrorBoundary>
      </group>
    )
  },
)

ModelLoader.displayName = "ModelLoader"

export function preloadModel(url: string) {
  if (url && !isStlUrl(url)) {
    useGLTF.preload(url)
  }
}
