import type { Object3D, Vector3, Plane, Color } from "three"
import type { PresetsType } from "@react-three/drei/helpers/environment-assets"

export type DisplayMode = "wireframe" | "shaded" | "normals" | "overhang"

export type LightingPreset = "none" | PresetsType

export interface CADViewportProps {
  modelUrl?: string
  model?: Object3D
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
  onModelLoaded?: (object: Object3D) => void
  onProgress?: (progress: number) => void
  onError?: (error: string) => void
  onLoadStart?: () => void
  className?: string
  children?: React.ReactNode
}

export interface DisplayModeApplierProps {
  mode: DisplayMode
  overhangAngle: number
  overhangAxis?: Vector3
  modelRef: React.RefObject<Object3D>
  clipPlanes: Plane[]
}

export interface ClippingPlaneProps {
  normal: [number, number, number]
  position: number
  onChange: (position: number) => void
  visible?: boolean
  okColor?: Color
}

export const DISPLAY_MODES: { value: DisplayMode; label: string; description: string }[] = [
  { value: "shaded", label: "Shaded Solid", description: "Smooth metallic/rough shading" },
  { value: "wireframe", label: "Wireframe", description: "Edges only" },
  { value: "normals", label: "Surface Normals", description: "Face normal coloring" },
  { value: "overhang", label: "Overhang Analysis", description: "Printable vs unsupported faces" },
]

export const LIGHTING_PRESETS: LightingPreset[] = [
  "none",
  "sunset",
  "dawn",
  "night",
  "warehouse",
  "forest",
  "apartment",
  "studio",
  "city",
  "park",
  "lobby",
]
