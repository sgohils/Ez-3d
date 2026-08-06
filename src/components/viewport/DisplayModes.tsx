"use client"

import {
  useEffect,
  useMemo,
  useRef,
  type FC,
  type RefObject,
} from "react"
import * as THREE from "three"
import { Box, Layers, Palette, Hammer } from "lucide-react"
import type { DisplayMode } from "./types"
import { DISPLAY_MODES } from "./types"

interface DisplayModeToggleProps {
  mode: DisplayMode
  onChange: (mode: DisplayMode) => void
  overhangAngle: number
  onOverhangAngleChange: (angle: number) => void
}

const ICONS: Record<DisplayMode, FC<any>> = {
  shaded: Box,
  wireframe: Layers,
  normals: Palette,
  overhang: Hammer,
}

export function DisplayModeToggle({
  mode,
  onChange,
  overhangAngle,
  onOverhangAngleChange,
}: DisplayModeToggleProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="inline-flex items-center gap-1 rounded-lg bg-gray-800/70 p-1 text-xs text-gray-300 backdrop-blur">
        {DISPLAY_MODES.map((d) => {
          const Icon = ICONS[d.value]
          const active = mode === d.value
          return (
            <button
              key={d.value}
              type="button"
              onClick={() => onChange(d.value)}
              title={d.description}
              className={
                active
                  ? "flex items-center gap-1.5 rounded-md bg-blue-600 px-2.5 py-1.5 text-white"
                  : "flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-gray-400 hover:text-gray-200 hover:bg-gray-700/50"
              }
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{d.label}</span>
            </button>
          )
        })}
      </div>

      {mode === "overhang" && (
        <div className="flex items-center gap-2.5 rounded-lg bg-gray-800/70 px-2.5 py-1.5 text-xs text-gray-300 backdrop-blur">
          <span>Overhang</span>
          <input
            type="range"
            min={1}
            max={89}
            step={1}
            value={overhangAngle}
            onChange={(e) => onOverhangAngleChange(Number(e.target.value))}
            className="flex-1 accent-blue-500"
          />
          <span className="w-10 text-right font-mono text-gray-200">
            {overhangAngle}°
          </span>
        </div>
      )}
    </div>
  )
}

const OVERHANG_VERTEX = /* glsl */ `
  varying vec3 vWorldNormal;
  varying vec3 vWorldPos;
  void main() {
    vWorldNormal = normalize((modelMatrix * vec4(normal, 0.0)).xyz);
    vWorldPos = (modelMatrix * vec4(position, 1.0)).xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`

const OVERHANG_FRAGMENT = /* glsl */ `
  varying vec3 vWorldNormal;
  varying vec3 vWorldPos;
  uniform vec3 uBuildAxis;
  uniform float uThreshold;
  uniform vec3 uOkColor;
  uniform vec3 uBadColor;
  uniform vec4 uClippingPlane;
  uniform float uUseClipping;
  void main() {
    float ndot = abs(dot(normalize(vWorldNormal), normalize(uBuildAxis)));
    float ang = acos(clamp(ndot, 0.0, 1.0));
    float overhang = smoothstep(uThreshold, 1.5707963, ang);
    vec3 color = mix(uOkColor, uBadColor, overhang);

    if (uUseClipping > 0.5) {
      float dist = dot(vWorldPos, uClippingPlane.xyz) - uClippingPlane.w;
      if (dist < 0.0) discard;
    }

    gl_FragColor = vec4(color, 1.0);
  }
`

function createOverhangMaterial(opts: {
  threshold: number
  clipPlane: THREE.Plane | null
  okColor: THREE.Color
  badColor: THREE.Color
  buildAxis: THREE.Vector3
}): THREE.ShaderMaterial {
  const m = new THREE.ShaderMaterial({
    uniforms: {
      uBuildAxis: { value: opts.buildAxis.clone().normalize() },
      uThreshold: { value: THREE.MathUtils.degToRad(opts.threshold) },
      uOkColor: { value: opts.okColor },
      uBadColor: { value: opts.badColor },
      uClippingPlane: { value: new THREE.Vector4() },
      uUseClipping: { value: opts.clipPlane ? 1 : 0 },
    },
    vertexShader: OVERHANG_VERTEX,
    fragmentShader: OVERHANG_FRAGMENT,
    side: THREE.DoubleSide,
    transparent: false,
    toneMapped: false,
  })
  if (opts.clipPlane) {
    m.uniforms.uClippingPlane.value.copy(opts.clipPlane.normal, 0)
    m.uniforms.uClippingPlane.value.w = opts.clipPlane.constant
  }
  m.uniformsNeedUpdate = true
  return m
}

const WIREFRAME_MATERIAL = new THREE.MeshBasicMaterial({
  color: "#9ca3af",
  wireframe: true,
})

const NORMALS_MATERIAL = new THREE.MeshNormalMaterial()

const DEFAULT_SHADED = new THREE.MeshStandardMaterial({
  color: "#c9b1ff",
  metalness: 0.2,
  roughness: 0.7,
})

interface DisplayModeApplierProps {
  mode: DisplayMode
  overhangAngle: number
  overhangAxis?: THREE.Vector3
  modelRef: RefObject<THREE.Object3D>
  clipPlane: THREE.Plane | null
  loadedToken?: number
  overhangOkColor?: THREE.Color
  overhangBadColor?: THREE.Color
}

interface Capture {
  map: Map<string, THREE.Material | THREE.Material[]>
  overhang: THREE.ShaderMaterial | null
}

export function DisplayModeApplier({
  mode,
  overhangAngle,
  overhangAxis = new THREE.Vector3(0, 1, 0),
  modelRef,
  clipPlane,
  loadedToken = 0,
  overhangOkColor = new THREE.Color("#22c55e"),
  overhangBadColor = new THREE.Color("#ef4444"),
}: DisplayModeApplierProps) {
  const captureRef = useRef<Capture | null>(null)

  const okColor = useMemo(() => overhangOkColor.clone(), [overhangOkColor])
  const badColor = useMemo(() => overhangBadColor.clone(), [overhangBadColor])

  useEffect(() => {
    const root = modelRef.current
    if (!root) return

    if (!captureRef.current) {
      captureRef.current = { map: new Map(), overhang: null }
    }
    const cap = captureRef.current

    root.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh)) return
      const mesh = obj
      if (cap.map.get(mesh.uuid) === undefined) {
        cap.map.set(mesh.uuid, mesh.material)
      }

      if (mode === "shaded") {
        const original = cap.map.get(mesh.uuid)
        mesh.material =
          original instanceof THREE.Material
            ? original
            : DEFAULT_SHADED
      } else if (mode === "wireframe") {
        mesh.material = WIREFRAME_MATERIAL
      } else if (mode === "normals") {
        mesh.material = NORMALS_MATERIAL
      } else if (mode === "overhang") {
        if (!cap.overhang) {
          cap.overhang = createOverhangMaterial({
            threshold: overhangAngle,
            clipPlane,
            okColor,
            badColor,
            buildAxis: overhangAxis,
          })
        }
        const overhang = cap.overhang
        overhang.uniforms.uThreshold.value =
          THREE.MathUtils.degToRad(overhangAngle)
        overhang.uniforms.uBuildAxis.value.copy(overhangAxis).normalize()
        overhang.uniforms.uOkColor.value = okColor
        overhang.uniforms.uBadColor.value = badColor
        if (clipPlane) {
          overhang.uniforms.uUseClipping.value = 1
          overhang.uniforms.uClippingPlane.value.set(
            clipPlane.normal.x,
            clipPlane.normal.y,
            clipPlane.normal.z,
            clipPlane.constant,
          )
        } else {
          overhang.uniforms.uUseClipping.value = 0
        }
        mesh.material = overhang
      }

      mesh.material.needsUpdate = true
    })
  }, [mode, overhangAngle, overhangAxis, clipPlane, okColor, badColor, modelRef, loadedToken])

  return null
}

export interface DisplayModesProps {
  mode: DisplayMode
  onModeChange: (mode: DisplayMode) => void
  overhangAngle: number
  onOverhangAngleChange: (angle: number) => void
  clippingEnabled: boolean
  onClippingChange: (enabled: boolean) => void
  clipPosition: number
  onClipPositionChange: (position: number) => void
  clipNormal: [number, number, number]
  onClipNormalChange: (normal: [number, number, number]) => void
}

const AXES: [string, [number, number, number]][] = [
  ["X", [1, 0, 0]],
  ["Y", [0, 1, 0]],
  ["Z", [0, 0, 1]],
]

export function DisplayModes({
  mode,
  onModeChange,
  overhangAngle,
  onOverhangAngleChange,
  clippingEnabled,
  onClippingChange,
  clipPosition,
  onClipPositionChange,
  clipNormal,
  onClipNormalChange,
}: DisplayModesProps) {
  const activeAxis = useMemo(() => {
    const a = clipNormal.map((v) => Math.abs(v))
    const idx = a.indexOf(Math.max(...a))
    return AXES[idx][0]
  }, [clipNormal])

  return (
    <div className="flex flex-col gap-2.5 rounded-lg bg-gray-800/70 p-3 text-xs/5 text-gray-300 backdrop-blur">
      <DisplayModeToggle
        mode={mode}
        onChange={onModeChange}
        overhangAngle={overhangAngle}
        onOverhangAngleChange={onOverhangAngleChange}
      />

      <div className="flex items-center justify-between rounded-md bg-gray-700/40 px-2.5 py-1.5">
        <span>Cross-section</span>
        <button
          type="button"
          onClick={() => onClippingChange(!clippingEnabled)}
          className={
            clippingEnabled
              ? "rounded-md bg-blue-600 px-2 py-0.5 text-xs text-white"
              : "rounded-md bg-gray-700 px-2 py-0.5 text-xs text-gray-300 hover:bg-gray-600"
          }
        >
          {clippingEnabled ? "On" : "Off"}
        </button>
      </div>

      {clippingEnabled && (
        <>
          <div className="flex items-center gap-2">
            <span>Axis</span>
            <div className="flex gap-1">
              {AXES.map(([label, axis]) => (
                <button
                  key={label}
                  type="button"
                  onClick={() => onClipNormalChange(axis)}
                  className={
                    activeAxis === label
                      ? "rounded bg-blue-600 px-1.5 py-0.5 text-xs text-white"
                      : "rounded bg-gray-700 px-1.5 py-0.5 text-xs text-gray-300 hover:bg-gray-600"
                  }
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <label className="w-14">Offset</label>
            <input
              type="range"
              min={-100}
              max={100}
              step={0.5}
              value={clipPosition}
              onChange={(e) => onClipPositionChange(Number(e.target.value))}
              className="flex-1 accent-blue-500"
            />
            <span className="w-10 text-right font-mono text-gray-200">
              {clipPosition.toFixed(1)}
            </span>
          </div>
        </>
      )}
    </div>
  )
}
