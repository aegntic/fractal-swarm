"use client"

import { useRef, useMemo, useState, useEffect } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, Stars } from '@react-three/drei'
import * as THREE from 'three'
import CloneNode from './CloneNode'
import ConnectionLines from './ConnectionLines'
import PerformanceParticles from './PerformanceParticles'
import CameraControls from './CameraControls'

interface Clone {
  id: string
  generation: number
  performance: number
  status: 'active' | 'inactive' | 'spawning'
  capital: number
  position?: [number, number, number]
  trades?: number
  winRate?: number
  strategy?: string
}

interface SwarmVisualizationProps {
  clones: Clone[]
  connections: Array<{ from: string; to: string; strength: number }>
  trades: Array<{ cloneId: string; profit: number; timestamp: number }>
  autoRotate?: boolean
  performanceMode?: 'quality' | 'performance'
}

export default function SwarmVisualization({
  clones,
  connections,
  trades,
  autoRotate = true,
  performanceMode = 'quality'
}: SwarmVisualizationProps) {
  const [hoveredClone, setHoveredClone] = useState<string | null>(null)
  const [selectedClone, setSelectedClone] = useState<string | null>(null)
  
  // Generate positions for clones in a 3D spiral pattern
  const clonePositions = useMemo(() => {
    const positions: Record<string, [number, number, number]> = {}
    
    clones.forEach((clone, index) => {
      if (clone.position) {
        positions[clone.id] = clone.position
      } else {
        // Create a 3D spiral distribution based on generation
        const angle = index * 0.5 + clone.generation * Math.PI * 0.25
        const radius = 5 + clone.generation * 3
        const height = clone.generation * 2 - 5
        
        positions[clone.id] = [
          Math.cos(angle) * radius,
          height + Math.sin(index * 0.3) * 2,
          Math.sin(angle) * radius
        ]
      }
    })
    
    return positions
  }, [clones])

  // Active trades for particle effects
  const activeTrades = useMemo(() => {
    const now = Date.now()
    return trades.filter(trade => now - trade.timestamp < 3000) // Show trades for 3 seconds
  }, [trades])

  return (
    <div className="w-full h-full relative bg-black">
      <Canvas
        gl={{ 
          antialias: performanceMode === 'quality',
          alpha: true,
          powerPreference: performanceMode === 'performance' ? 'low-power' : 'high-performance'
        }}
        shadows={performanceMode === 'quality'}
      >
        <PerspectiveCamera makeDefault position={[20, 15, 20]} fov={60} />
        
        {/* Lighting */}
        <ambientLight intensity={0.2} />
        <pointLight position={[10, 10, 10]} intensity={0.5} color="#00ffff" />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#ff00ff" />
        
        {/* Background */}
        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
        
        {/* Grid */}
        <gridHelper args={[50, 50, '#1a1a2e', '#16213e']} />
        
        {/* Clone Nodes */}
        {clones.map((clone) => (
          <CloneNode
            key={clone.id}
            clone={clone}
            position={clonePositions[clone.id]}
            isHovered={hoveredClone === clone.id}
            isSelected={selectedClone === clone.id}
            onHover={(hovered) => setHoveredClone(hovered ? clone.id : null)}
            onClick={() => setSelectedClone(clone.id === selectedClone ? null : clone.id)}
          />
        ))}
        
        {/* Connections */}
        <ConnectionLines
          connections={connections}
          clonePositions={clonePositions}
          hoveredClone={hoveredClone}
          selectedClone={selectedClone}
        />
        
        {/* Performance Particles */}
        {activeTrades.map((trade, index) => {
          const position = clonePositions[trade.cloneId]
          if (!position) return null
          
          return (
            <PerformanceParticles
              key={`${trade.cloneId}-${trade.timestamp}-${index}`}
              startPosition={position}
              profit={trade.profit}
              color={trade.profit > 0 ? '#00ff00' : '#ff0000'}
            />
          )
        })}
        
        {/* Camera Controls */}
        <CameraControls autoRotate={autoRotate} target={[0, 0, 0]} />
        
        {/* Post-processing effects disabled for compatibility */}
      </Canvas>
      
      {/* Clone Info Panel */}
      {selectedClone && (
        <div className="absolute top-4 right-4 bg-black/80 backdrop-blur-md border border-cyan-500/30 rounded-lg p-4 text-white max-w-xs">
          <h3 className="text-cyan-400 font-bold mb-2">Clone Details</h3>
          {(() => {
            const clone = clones.find(c => c.id === selectedClone)
            if (!clone) return null
            
            return (
              <div className="space-y-2 text-sm">
                <div>ID: <span className="text-cyan-300">{clone.id.slice(0, 8)}...</span></div>
                <div>Generation: <span className="text-purple-400">Gen {clone.generation}</span></div>
                <div>Capital: <span className="text-green-400">${clone.capital.toFixed(2)}</span></div>
                <div>Performance: <span className="text-yellow-400">{(clone.performance * 100).toFixed(1)}%</span></div>
                {clone.trades && <div>Trades: <span className="text-blue-400">{clone.trades}</span></div>}
                {clone.winRate && <div>Win Rate: <span className="text-green-400">{(clone.winRate * 100).toFixed(1)}%</span></div>}
                {clone.strategy && <div>Strategy: <span className="text-purple-300">{clone.strategy}</span></div>}
                <div>Status: <span className={`${
                  clone.status === 'active' ? 'text-green-400' : 
                  clone.status === 'spawning' ? 'text-yellow-400' : 
                  'text-red-400'
                }`}>{clone.status}</span></div>
              </div>
            )
          })()}
        </div>
      )}
      
      {/* Performance Mode Toggle */}
      <div className="absolute bottom-4 left-4 text-white/60 text-xs">
        Performance Mode: {performanceMode}
      </div>
    </div>
  )
}