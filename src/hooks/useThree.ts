import * as THREE from "three"

export function useThreeHelpers() {
  return {
    BoxGeometry: THREE.BoxGeometry,
    MeshStandardMaterial: THREE.MeshStandardMaterial,
  }
}
