'use client';

import React from 'react';
import ChartWrapper from './ChartWrapper';

export default function SimpleAreaChart() {
  // Generate smooth portfolio value data
  const dataPoints = Array.from({ length: 30 }, (_, i) => {
    const baseValue = 100000;
    const growth = 1.002; // 0.2% daily growth
    const noise = Math.sin(i / 5) * 0.02 + (Math.random() - 0.5) * 0.01;
    return baseValue * Math.pow(growth, i) * (1 + noise);
  });

  const minValue = Math.min(...dataPoints);
  const maxValue = Math.max(...dataPoints);
  const valueRange = maxValue - minValue;
  
  const chartWidth = 600;
  const chartHeight = 300;
  
  const points = dataPoints.map((value, i) => {
    const x = (i / (dataPoints.length - 1)) * chartWidth;
    const y = chartHeight - ((value - minValue) / valueRange) * chartHeight;
    return `${x},${y}`;
  }).join(' ');
  
  const areaPoints = `0,${chartHeight} ${points} ${chartWidth},${chartHeight}`;

  return (
    <ChartWrapper height={300}>
      <div className="w-full h-full relative">
        <svg 
          width="100%" 
          height="100%" 
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          preserveAspectRatio="none"
        >
          {/* Gradient definition */}
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#06ffa5" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#06ffa5" stopOpacity="0" />
            </linearGradient>
          </defs>
          
          {/* Grid lines */}
          {[0, 0.5, 1].map((y, i) => (
            <line
              key={i}
              x1="0"
              y1={y * chartHeight}
              x2={chartWidth}
              y2={y * chartHeight}
              stroke="rgba(255,255,255,0.05)"
              strokeWidth="1"
            />
          ))}
          
          {/* Area fill */}
          <polygon
            points={areaPoints}
            fill="url(#areaGradient)"
          />
          
          {/* Line */}
          <polyline
            points={points}
            fill="none"
            stroke="#06ffa5"
            strokeWidth="2"
          />
          
          {/* Data points */}
          {dataPoints.map((value, i) => {
            const x = (i / (dataPoints.length - 1)) * chartWidth;
            const y = chartHeight - ((value - minValue) / valueRange) * chartHeight;
            
            if (i % 5 === 0 || i === dataPoints.length - 1) {
              return (
                <circle
                  key={i}
                  cx={x}
                  cy={y}
                  r="3"
                  fill="#06ffa5"
                  className="opacity-80"
                />
              );
            }
            return null;
          })}
        </svg>
        
        {/* Value display */}
        <div className="absolute top-4 left-4">
          <div className="text-2xl font-light text-white">
            ${dataPoints[dataPoints.length - 1].toFixed(0).toLocaleString()}
          </div>
          <div className="text-sm text-green-400">
            ▲ +{((dataPoints[dataPoints.length - 1] - dataPoints[0]) / dataPoints[0] * 100).toFixed(2)}%
          </div>
        </div>
      </div>
    </ChartWrapper>
  );
}