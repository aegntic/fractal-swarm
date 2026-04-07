'use client';

import dynamic from 'next/dynamic';
import { Suspense } from 'react';

// Dynamic import to avoid SSR issues with Three.js
const SwarmVisualization = dynamic(
  () => import('@/components/3d/SwarmVisualization'),
  { 
    ssr: false,
    loading: () => (
      <div className="w-full h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
          <p className="text-white">Loading 3D Swarm Visualization...</p>
        </div>
      </div>
    )
  }
);

export default function Swarm3DPage() {
  return (
    <div className="w-full h-screen overflow-hidden">
      <Suspense fallback={<div className="w-full h-screen bg-gray-900" />}>
        <SwarmVisualization 
          clones={[
            { id: 'clone-1', generation: 0, performance: 0.15, status: 'active', capital: 150, trades: 25, winRate: 0.72, strategy: 'MEV Hunter' },
            { id: 'clone-2', generation: 1, performance: 0.23, status: 'active', capital: 230, trades: 18, winRate: 0.83, strategy: 'Arbitrage' },
            { id: 'clone-3', generation: 1, performance: -0.05, status: 'inactive', capital: 95, trades: 12, winRate: 0.42, strategy: 'Grid Trading' },
            { id: 'clone-4', generation: 2, performance: 0.34, status: 'spawning', capital: 340, trades: 8, winRate: 0.88, strategy: 'Flash Loan' }
          ]}
          connections={[
            { from: 'clone-1', to: 'clone-2', strength: 0.8 },
            { from: 'clone-1', to: 'clone-3', strength: 0.3 },
            { from: 'clone-2', to: 'clone-4', strength: 0.9 }
          ]}
          trades={[]}
        />
      </Suspense>
    </div>
  );
}