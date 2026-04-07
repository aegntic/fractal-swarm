"use client"

import { useRef, useState, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import { Sphere, Text, Billboard } from '@react-three/drei'
import * as THREE from 'three'

interface CloneNodeProps {
  clone: {
    id: string
    generation: number
    performance: number
    status: 'active' | 'inactive' | 'spawning'
    capital: number
  }
  position: [number, number, number]
  isHovered: boolean
  isSelected: boolean
  onHover: (hovered: boolean) => void
  onClick: () => void
}

export default function CloneNode({
  clone,
  position,
  isHovered,
  isSelected,
  onHover,
  onClick
}: CloneNodeProps) {
  const meshRef = useRef<THREE.Mesh>(null)
  const glowRef = useRef<THREE.Mesh>(null)
  const [pulsePhase, setPulsePhase] = useState(0)
  
  // Calculate node size based on capital
  const nodeSize = Math.max(0.5, Math.min(2, Math.log10(clone.capital + 1) * 0.5))
  
  // Color based on status and performance
  const getColor = () => {
    if (clone.status === 'inactive') return '#666666'
    if (clone.status === 'spawning') return '#ffff00'
    
    // Active nodes: color based on performance
    const hue = clone.performance * 120 // 0 = red, 120 = green
    return `hsl(${hue}, 100%, 50%)`
  }
  
  const color = getColor()
  
  // Animate the node
  useFrame((state, delta) => {
    if (!meshRef.current || !glowRef.current) return
    
    // Pulse effect for active nodes
    if (clone.status === 'active') {
      setPulsePhase(prev => (prev + delta * 2) % (Math.PI * 2))
      const pulseFactor = 1 + Math.sin(pulsePhase) * 0.1
      meshRef.current.scale.setScalar(nodeSize * pulseFactor)
      
      // Glow intensity based on performance
      const glowIntensity = 0.5 + clone.performance * 0.5
      glowRef.current.scale.setScalar(nodeSize * (1.5 + Math.sin(pulsePhase) * 0.2))
      
      if (glowRef.current.material && 'opacity' in glowRef.current.material) {
        glowRef.current.material.opacity = glowIntensity * (0.3 + Math.sin(pulsePhase) * 0.1)
      }
    }
    
    // Rotation for spawning nodes
    if (clone.status === 'spawning') {
      meshRef.current.rotation.y += delta * 2
      meshRef.current.rotation.z += delta * 1.5
    }
    
    // Hover effect
    if (isHovered) {
      meshRef.current.scale.setScalar(nodeSize * 1.2)
    }
  })
  
  return (
    <group position={position}>
      {/* Glow effect */}
      <Sphere
        ref={glowRef}
        args={[nodeSize * 1.5, 16, 16]}
        material-transparent
        material-opacity={0.3}
        material-color={color}
        material-emissive={color}
        material-emissiveIntensity={0.5}
        renderOrder={-1}
      />
      
      {/* Main node */}
      <Sphere
        ref={meshRef}
        args={[nodeSize, 32, 32]}
        onPointerOver={(e) => {
          e.stopPropagation()
          onHover(true)
        }}
        onPointerOut={(e) => {
          e.stopPropagation()
          onHover(false)
        }}
        onClick={(e) => {
          e.stopPropagation()
          onClick()
        }}
      >
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.5}
          metalness={0.8}
          roughness={0.2}
        />
      </Sphere>
      
      {/* Inner core for active nodes */}
      {clone.status === 'active' && (
        <Sphere args={[nodeSize * 0.3, 16, 16]}>
          <meshBasicMaterial color="#ffffff" />
        </Sphere>
      )}
      
      {/* Generation rings */}
      {Array.from({ length: clone.generation }, (_, i) => (
        <mesh key={i} rotation-x={Math.PI / 2}>
          <ringGeometry args={[
            nodeSize + 0.3 + i * 0.2,
            nodeSize + 0.4 + i * 0.2,
            32
          ]} />
          <meshBasicMaterial
            color={color}
            transparent
            opacity={0.3 - i * 0.05}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}
      
      {/* Labels */}
      {(isHovered || isSelected) && (
        <Billboard
          follow={true}
          lockX={false}
          lockY={false}
          lockZ={false}
          position={[0, nodeSize + 1, 0]}
        >
          <Text
            fontSize={0.5}
            color="white"
            anchorX="center"
            anchorY="bottom"
            outlineWidth={0.1}
            outlineColor="black"
          >
            {`Gen ${clone.generation}`}
          </Text>
          <Text
            fontSize={0.3}
            color={color}
            anchorX="center"
            anchorY="top"
            position={[0, -0.2, 0]}
          >
            {`$${clone.capital.toFixed(0)}`}
          </Text>
        </Billboard>
      )}
      
      {/* Status indicator */}
      {clone.status === 'spawning' && (
        <pointLight
          color="#ffff00"
          intensity={2}
          distance={5}
          decay={2}
        />
      )}
    </group>
  )
}