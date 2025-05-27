"use client"

import { useRef, useEffect } from 'react'
import { useThree, useFrame } from '@react-three/fiber'
import { OrbitControls as OrbitControlsImpl } from '@react-three/drei'
import * as THREE from 'three'

interface CameraControlsProps {
  autoRotate?: boolean
  target?: [number, number, number]
  minDistance?: number
  maxDistance?: number
  enableDamping?: boolean
  dampingFactor?: number
  rotateSpeed?: number
  zoomSpeed?: number
  enablePan?: boolean
  minPolarAngle?: number
  maxPolarAngle?: number
}

export default function CameraControls({
  autoRotate = true,
  target = [0, 0, 0],
  minDistance = 10,
  maxDistance = 100,
  enableDamping = true,
  dampingFactor = 0.05,
  rotateSpeed = 0.5,
  zoomSpeed = 1,
  enablePan = true,
  minPolarAngle = Math.PI * 0.1,
  maxPolarAngle = Math.PI * 0.9
}: CameraControlsProps) {
  const controlsRef = useRef<any>(null)
  const { camera, gl } = useThree()
  const autoRotateSpeed = useRef(0.5)
  const targetRotation = useRef(0)
  
  // Smooth camera transitions
  useEffect(() => {
    if (camera) {
      // Set initial camera position for a good view
      camera.position.set(30, 20, 30)
      camera.lookAt(new THREE.Vector3(...target))
    }
  }, [camera, target])
  
  // Custom auto-rotate with varying speed
  useFrame((state, delta) => {
    if (!controlsRef.current || !autoRotate) return
    
    // Vary rotation speed with a sine wave for organic movement
    const time = state.clock.elapsedTime
    autoRotateSpeed.current = 0.3 + Math.sin(time * 0.1) * 0.2
    
    // Apply rotation
    targetRotation.current += autoRotateSpeed.current * delta
    controlsRef.current.setAzimuthalAngle(targetRotation.current)
  })
  
  // Handle user interaction
  const handleUserInteraction = () => {
    // Pause auto-rotation when user interacts
    if (autoRotate && controlsRef.current) {
      targetRotation.current = controlsRef.current.getAzimuthalAngle()
    }
  }
  
  return (
    <OrbitControlsImpl
      ref={controlsRef}
      args={[camera, gl.domElement]}
      target={target}
      minDistance={minDistance}
      maxDistance={maxDistance}
      enableDamping={enableDamping}
      dampingFactor={dampingFactor}
      rotateSpeed={rotateSpeed}
      zoomSpeed={zoomSpeed}
      enablePan={enablePan}
      minPolarAngle={minPolarAngle}
      maxPolarAngle={maxPolarAngle}
      autoRotate={false} // We handle auto-rotation manually
      onStart={handleUserInteraction}
      makeDefault
    />
  )
}