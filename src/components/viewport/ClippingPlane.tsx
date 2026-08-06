"use client"

import {
  useEffect,
  useMemo,
  useRef,
  type FC,
  type RefObject,
} from "react"
import * as THREE from "three"
import { useThree } from "@react-three/fiber"
import type { ThreeEvent } from "@react-three/fiber"
import type { ClippingPlaneProps } from "./types"

const DRAG_PLANE_SIZE = 200

export const ClippingPlane: FC<ClippingPlaneProps> = ({
  normal,
  position,
  onChange,
  visible = true,
}) => {
  const { camera, gl } = useThree()
  const domElement = gl.domElement

  const normalVec = useMemo(
    () => new THREE.Vector3(...normal).normalize(),
    [normal],
  )

  const plane = useMemo(
    () => new THREE.Plane(normalVec.clone(), position),
    [normalVec, position],
  )

  const raycaster = useMemo(() => new THREE.Raycaster(), [])
  const mouse = useMemo(() => new THREE.Vector2(), [])
  const scratch = useMemo(() => new THREE.Vector3(), [])
  const meshRef = useRef<THREE.Mesh>(null!)
  const draggingRef = useRef<{ active: boolean; base: number }>({
    active: false,
    base: 0,
  })
  const moveHandlerRef = useRef<(ev: PointerEvent) => void>(() => {})
  const upHandlerRef = useRef<(ev: PointerEvent) => void>(() => {})

  useEffect(() => {
    plane.normal.copy(normalVec)
    plane.constant = position
  }, [plane, normalVec, position])

  useEffect(() => {
    gl.clippingPlanes = [plane]
    gl.localClippingEnabled = false
    return () => {
      gl.clippingPlanes = []
    }
  }, [gl, plane])

  function updateOrientation() {
    if (!meshRef.current) return
    meshRef.current.position
      .copy(normalVec)
      .multiplyScalar(position)
    meshRef.current.quaternion.setFromUnitVectors(
      new THREE.Vector3(0, 0, 1),
      normalVec,
    )
  }

  useEffect(() => {
    updateOrientation()
  })

  const projectOntoPlane = (clientX: number, clientY: number): THREE.Vector3 | null => {
    const rect = domElement.getBoundingClientRect()
    mouse.x = ((clientX - rect.left) / rect.width) * 2 - 1
    mouse.y = -((clientY - rect.top) / rect.height) * 2 + 1
    raycaster.setFromCamera(mouse, camera)
    return raycaster.ray.intersectPlane(plane, scratch)
  }

  const handlePointerDown = (event: ThreeEvent<PointerEvent>) => {
    event.stopPropagation()
    const point = projectOntoPlane(event.clientX, event.clientY)
    if (!point) return
    draggingRef.current.active = true
    draggingRef.current.base = point.dot(normalVec)

    const onMove = (ev: PointerEvent) => {
      if (!draggingRef.current.active) return
      const p = projectOntoPlane(ev.clientX, ev.clientY)
      if (!p) return
      const delta = p.dot(normalVec) - draggingRef.current.base
      onChange(position + delta)
    }
    const onUp = () => {
      draggingRef.current.active = false
      domElement.ownerDocument.removeEventListener("pointermove", moveHandlerRef.current)
      domElement.ownerDocument.removeEventListener("pointerup", upHandlerRef.current)
    }
    moveHandlerRef.current = onMove
    upHandlerRef.current = onUp
    domElement.ownerDocument.addEventListener("pointermove", onMove)
    domElement.ownerDocument.addEventListener("pointerup", onUp)
  }

  if (!visible) return null

  return (
    <mesh
      ref={meshRef}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerDown}
      onPointerUp={() => {
        draggingRef.current.active = false
      }}
      onPointerLeave={() => {
        draggingRef.current.active = false
      }}
    >
      <planeGeometry args={[DRAG_PLANE_SIZE, DRAG_PLANE_SIZE, 1, 1]} />
      <meshBasicMaterial
        color="#38bdf8"
        transparent
        opacity={0.1}
        side={THREE.DoubleSide}
        depthWrite={false}
        toneMapped={false}
      />
    </mesh>
  )
}
