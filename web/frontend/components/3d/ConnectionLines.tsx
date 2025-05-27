"use client"

import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { CatmullRomCurve3, BufferGeometry } from 'three'

interface ConnectionLinesProps {
  connections: Array<{ from: string; to: string; strength: number }>
  clonePositions: Record<string, [number, number, number]>
  hoveredClone: string | null
  selectedClone: string | null
}

interface AnimatedConnectionProps {
  start: THREE.Vector3
  end: THREE.Vector3
  strength: number
  isHighlighted: boolean
  color: string
}

function AnimatedConnection({ start, end, strength, isHighlighted, color }: AnimatedConnectionProps) {
  const lineRef = useRef<THREE.Line>(null)
  const particlesRef = useRef<THREE.Points>(null)
  const materialRef = useRef<THREE.LineBasicMaterial>(null)
  
  // Create curved path between nodes
  const curve = useMemo(() => {
    const midPoint = new THREE.Vector3()
      .addVectors(start, end)
      .multiplyScalar(0.5)
    
    // Add some curvature
    const distance = start.distanceTo(end)
    midPoint.y += distance * 0.2
    
    return new CatmullRomCurve3([start, midPoint, end])
  }, [start, end])
  
  // Generate points along the curve
  const points = useMemo(() => curve.getPoints(50), [curve])
  
  // Create particle positions along the line
  const particlePositions = useMemo(() => {
    const positions = new Float32Array(30) // 10 particles * 3 coordinates
    for (let i = 0; i < 10; i++) {
      const t = i / 10
      const point = curve.getPoint(t)
      positions[i * 3] = point.x
      positions[i * 3 + 1] = point.y
      positions[i * 3 + 2] = point.z
    }
    return positions
  }, [curve])
  
  // Animate particles along the connection
  useFrame((state) => {
    if (!particlesRef.current) return
    
    const time = state.clock.elapsedTime
    const positions = particlesRef.current.geometry.attributes.position.array as Float32Array
    
    for (let i = 0; i < 10; i++) {
      const t = ((time * strength * 0.2 + i / 10) % 1)
      const point = curve.getPoint(t)
      positions[i * 3] = point.x
      positions[i * 3 + 1] = point.y
      positions[i * 3 + 2] = point.z
    }
    
    particlesRef.current.geometry.attributes.position.needsUpdate = true
    
    // Pulse the line opacity
    if (materialRef.current) {
      materialRef.current.opacity = isHighlighted 
        ? 0.6 + Math.sin(time * 3) * 0.2 
        : 0.2 + Math.sin(time * 2) * 0.1
    }
  })
  
  return (
    <group>
      {/* Connection line */}
      <line>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={points.length}
            array={new Float32Array(points.flatMap(p => [p.x, p.y, p.z]))}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial
          ref={materialRef}
          color={color}
          transparent
          opacity={isHighlighted ? 0.6 : 0.2}
          linewidth={isHighlighted ? 3 : 1}
        />
      </line>
      
      {/* Animated particles */}
      <points ref={particlesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={10}
            array={particlePositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={strength * 0.1 + 0.05}
          color={color}
          transparent
          opacity={0.8}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
        />
      </points>
    </group>
  )
}

export default function ConnectionLines({
  connections,
  clonePositions,
  hoveredClone,
  selectedClone
}: ConnectionLinesProps) {
  // Filter and enhance connections
  const enhancedConnections = useMemo(() => {
    return connections
      .filter(conn => clonePositions[conn.from] && clonePositions[conn.to])
      .map(conn => {
        const fromPos = clonePositions[conn.from]
        const toPos = clonePositions[conn.to]
        
        const isHighlighted = 
          hoveredClone === conn.from || 
          hoveredClone === conn.to ||
          selectedClone === conn.from ||
          selectedClone === conn.to
        
        // Color based on strength and highlight
        let color = '#00ffff'
        if (conn.strength > 0.7) color = '#ff00ff'
        else if (conn.strength > 0.4) color = '#00ff00'
        if (isHighlighted) color = '#ffffff'
        
        return {
          ...conn,
          start: new THREE.Vector3(...fromPos),
          end: new THREE.Vector3(...toPos),
          isHighlighted,
          color
        }
      })
  }, [connections, clonePositions, hoveredClone, selectedClone])
  
  return (
    <group>
      {enhancedConnections.map((conn, index) => (
        <AnimatedConnection
          key={`${conn.from}-${conn.to}-${index}`}
          start={conn.start}
          end={conn.end}
          strength={conn.strength}
          isHighlighted={conn.isHighlighted}
          color={conn.color}
        />
      ))}
    </group>
  )
}