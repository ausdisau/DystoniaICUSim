import { useEffect, useRef } from 'react'
import * as THREE from 'three'

export function ThreeScene() {
  const mountRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 100)
    camera.position.set(0, 1, 3)

    const renderer = new THREE.WebGLRenderer({ antialias: true })
    mount.appendChild(renderer.domElement)

    const resize = () => {
      const w = mount.clientWidth || 400
      const h = mount.clientHeight || 300
      renderer.setSize(w, h, false)
      camera.aspect = w / h
      camera.updateProjectionMatrix()
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(mount)

    const light = new THREE.HemisphereLight(0xffffff, 0x222222, 1)
    scene.add(light)

    const geo = new THREE.SphereGeometry(0.5, 32, 32)
    const mat = new THREE.MeshStandardMaterial({ color: 0x2aa9d2, roughness: 0.4 })
    const mesh = new THREE.Mesh(geo, mat)
    scene.add(mesh)

    let raf = 0
    const animate = () => {
      mesh.rotation.y += 0.01
      renderer.render(scene, camera)
      raf = requestAnimationFrame(animate)
    }
    raf = requestAnimationFrame(animate)

    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
      renderer.dispose()
      mount.removeChild(renderer.domElement)
    }
  }, [])

  return (
    <div role="region" aria-label="3D Scene" ref={mountRef} style={{ width: '100%', height: 240, border: '1px solid #ddd', borderRadius: 8 }} />
  )
}
