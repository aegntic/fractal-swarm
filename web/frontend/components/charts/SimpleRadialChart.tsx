'use client';

import React from 'react';
import ChartWrapper from './ChartWrapper';

interface MetricData {
  label: string;
  value: number;
  color: string;
}

export default function SimpleRadialChart() {
  const metrics: MetricData[] = [
    { label: 'Win Rate', value: 87, color: '#06ffa5' },
    { label: 'ROI', value: 92, color: '#1890ff' },
    { label: 'Efficiency', value: 78, color: '#7c3aed' },
    { label: 'Risk Score', value: 23, color: '#f97316' },
  ];

  const centerX = 150;
  const centerY = 150;
  const maxRadius = 120;
  const strokeWidth = 12;

  return (
    <ChartWrapper height={350}>
      <div className="w-full h-full flex items-center justify-center">
        <div className="relative">
          <svg width="300" height="300" viewBox="0 0 300 300">
            {metrics.map((metric, i) => {
              const radius = maxRadius - (i * 25);
              const circumference = 2 * Math.PI * radius;
              const strokeDasharray = `${(metric.value / 100) * circumference} ${circumference}`;
              const rotation = -90; // Start from top
              
              return (
                <g key={i}>
                  {/* Background circle */}
                  <circle
                    cx={centerX}
                    cy={centerY}
                    r={radius}
                    fill="none"
                    stroke="rgba(255,255,255,0.05)"
                    strokeWidth={strokeWidth}
                  />
                  
                  {/* Progress circle */}
                  <circle
                    cx={centerX}
                    cy={centerY}
                    r={radius}
                    fill="none"
                    stroke={metric.color}
                    strokeWidth={strokeWidth}
                    strokeDasharray={strokeDasharray}
                    strokeLinecap="round"
                    transform={`rotate(${rotation} ${centerX} ${centerY})`}
                    className="transition-all duration-1000 ease-out"
                    style={{
                      filter: `drop-shadow(0 0 8px ${metric.color}40)`
                    }}
                  />
                </g>
              );
            })}
            
            {/* Center text */}
            <text
              x={centerX}
              y={centerY}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-white"
            >
              <tspan x={centerX} dy="-10" className="text-3xl font-light">85%</tspan>
              <tspan x={centerX} dy="30" className="text-sm opacity-60">Overall</tspan>
            </text>
          </svg>
          
          {/* Legend */}
          <div className="absolute -right-32 top-1/2 transform -translate-y-1/2">
            <div className="space-y-3">
              {metrics.map((metric, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: metric.color }}
                  />
                  <div className="text-sm">
                    <div className="text-neutral-400">{metric.label}</div>
                    <div className="text-white font-medium">{metric.value}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </ChartWrapper>
  );
}