"use client"

import { useRef, useMemo, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { Text } from '@react-three/drei'

interface PerformanceParticlesProps {
  startPosition: [number, number, number]
  profit: number
  color: string
}

export default function PerformanceParticles({
  startPosition,
  profit,
  color
}: PerformanceParticlesProps) {
  const particlesRef = useRef<THREE.Points>(null)
  const textRef = useRef<THREE.Group>(null)
  const startTime = useRef(Date.now())
  const lifetime = 3000 // 3 seconds
  
  // Generate particle data
  const particleData = useMemo(() => {
    const particleCount = Math.min(50, Math.abs(profit) * 10 + 10)
    const positions = new Float32Array(particleCount * 3)
    const velocities = new Float32Array(particleCount * 3)
    const sizes = new Float32Array(particleCount)
    const lifetimes = new Float32Array(particleCount)
    
    for (let i = 0; i < particleCount; i++) {
      // Initial position at start point
      positions[i * 3] = startPosition[0]
      positions[i * 3 + 1] = startPosition[1]
      positions[i * 3 + 2] = startPosition[2]
      
      // Random velocities in a cone shape
      const angle = Math.random() * Math.PI * 2
      const speed = 0.5 + Math.random() * 1.5
      const upwardBias = profit > 0 ? 1.5 : -0.5
      
      velocities[i * 3] = Math.cos(angle) * speed * 0.3
      velocities[i * 3 + 1] = upwardBias + Math.random() * 0.5
      velocities[i * 3 + 2] = Math.sin(angle) * speed * 0.3
      
      // Random sizes
      sizes[i] = 0.05 + Math.random() * 0.15
      
      // Staggered lifetimes
      lifetimes[i] = Math.random() * 0.3
    }
    
    return {
      positions,
      velocities,
      sizes,
      lifetimes,
      particleCount
    }
  }, [startPosition, profit])
  
  // Animate particles
  useFrame((state, delta) => {
    if (!particlesRef.current) return
    
    const elapsed = Date.now() - startTime.current
    const progress = elapsed / lifetime
    
    if (progress > 1) {
      // Remove particles after lifetime
      if (particlesRef.current.parent) {
        particlesRef.current.parent.remove(particlesRef.current)
      }
      return
    }
    
    const positions = particlesRef.current.geometry.attributes.position.array as Float32Array
    const sizes = particlesRef.current.geometry.attributes.size.array as Float32Array
    
    for (let i = 0; i < particleData.particleCount; i++) {
      const particleProgress = Math.min(1, progress / (1 - particleData.lifetimes[i]))
      
      if (particleProgress > 0) {
        // Update position with velocity and gravity
        positions[i * 3] += particleData.velocities[i * 3] * delta
        positions[i * 3 + 1] += particleData.velocities[i * 3 + 1] * delta - delta * 0.5 * particleProgress
        positions[i * 3 + 2] += particleData.velocities[i * 3 + 2] * delta
        
        // Fade out particles
        sizes[i] = particleData.sizes[i] * (1 - particleProgress * 0.8)
      }
    }
    
    particlesRef.current.geometry.attributes.position.needsUpdate = true
    particlesRef.current.geometry.attributes.size.needsUpdate = true
    
    // Animate text
    if (textRef.current) {
      textRef.current.position.y = startPosition[1] + progress * 3
      textRef.current.scale.setScalar(1 + progress * 0.5)
      
      if (textRef.current.children[0] && 'material' in textRef.current.children[0]) {
        const material = textRef.current.children[0].material as THREE.Material
        if ('opacity' in material) {
          material.opacity = 1 - progress
        }
      }
    }
  })
  
  // Custom shader material for particles
  const particleMaterial = useMemo(() => {
    return new THREE.ShaderMaterial({
      uniforms: {
        color: { value: new THREE.Color(color) },
        time: { value: 0 }
      },
      vertexShader: `
        attribute float size;
        varying float vAlpha;
        
        void main() {
          vAlpha = size / 0.2; // Alpha based on size
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = size * (300.0 / -mvPosition.z);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        uniform vec3 color;
        varying float vAlpha;
        
        void main() {
          float r = distance(gl_PointCoord, vec2(0.5));
          if (r > 0.5) discard;
          
          float alpha = (1.0 - r * 2.0) * vAlpha;
          gl_FragColor = vec4(color, alpha);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })
  }, [color])
  
  return (
    <group>
      {/* Particle system */}
      <points ref={particlesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={particleData.particleCount}
            array={particleData.positions}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-size"
            count={particleData.particleCount}
            array={particleData.sizes}
            itemSize={1}
          />
        </bufferGeometry>
        <primitive object={particleMaterial} />
      </points>
      
      {/* Profit/Loss text */}
      <group ref={textRef} position={startPosition}>
        <Text
          fontSize={0.5}
          color={color}
          anchorX="center"
          anchorY="middle"
          outlineWidth={0.05}
          outlineColor="black"
          material-transparent
          material-opacity={1}
        >
          {profit > 0 ? '+' : ''}{profit.toFixed(2)}
        </Text>
      </group>
      
      {/* Impact ring effect for large trades */}
      {Math.abs(profit) > 50 && (
        <mesh position={startPosition} rotation-x={-Math.PI / 2}>
          <ringGeometry args={[0, Math.abs(profit) / 20, 32]} />
          <meshBasicMaterial
            color={color}
            transparent
            opacity={0.3}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}
    </group>
  )
}