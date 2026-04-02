'use client';

import React from 'react';
import ChartWrapper from './ChartWrapper';

export default function SimpleCandlestickChart() {
  // Simple SVG-based candlestick chart for guaranteed rendering
  const candles = Array.from({ length: 50 }, (_, i) => {
    const basePrice = 45000;
    const volatility = 0.02;
    const trend = Math.sin(i / 10) * 0.01;
    
    const open = basePrice * (1 + (Math.random() - 0.5) * volatility + trend * i);
    const close = open * (1 + (Math.random() - 0.5) * volatility);
    const high = Math.max(open, close) * (1 + Math.random() * volatility * 0.5);
    const low = Math.min(open, close) * (1 - Math.random() * volatility * 0.5);
    
    return { open, close, high, low, isGreen: close > open };
  });

  const minPrice = Math.min(...candles.map(c => c.low));
  const maxPrice = Math.max(...candles.map(c => c.high));
  const priceRange = maxPrice - minPrice;
  
  const chartWidth = 800;
  const chartHeight = 400;
  const candleWidth = chartWidth / candles.length;
  
  const priceToY = (price: number) => {
    return chartHeight - ((price - minPrice) / priceRange) * chartHeight;
  };

  return (
    <ChartWrapper height={450}>
      <div className="w-full h-full relative">
        {/* Price labels */}
        <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-neutral-500">
          <span>${maxPrice.toFixed(0)}</span>
          <span>${((maxPrice + minPrice) / 2).toFixed(0)}</span>
          <span>${minPrice.toFixed(0)}</span>
        </div>
        
        {/* Chart */}
        <svg 
          width="100%" 
          height="100%" 
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          preserveAspectRatio="none"
          className="pl-12"
        >
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((y, i) => (
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
          
          {/* Candles */}
          {candles.map((candle, i) => {
            const x = i * candleWidth + candleWidth / 2;
            const color = candle.isGreen ? '#06ffa5' : '#ef4444';
            
            return (
              <g key={i}>
                {/* Wick */}
                <line
                  x1={x}
                  y1={priceToY(candle.high)}
                  x2={x}
                  y2={priceToY(candle.low)}
                  stroke={color}
                  strokeWidth="1"
                  opacity="0.6"
                />
                
                {/* Body */}
                <rect
                  x={x - candleWidth * 0.3}
                  y={priceToY(Math.max(candle.open, candle.close))}
                  width={candleWidth * 0.6}
                  height={Math.abs(priceToY(candle.open) - priceToY(candle.close))}
                  fill={color}
                  opacity="0.8"
                />
              </g>
            );
          })}
        </svg>
        
        {/* Current price indicator */}
        <div className="absolute right-4 top-4">
          <div className="text-3xl font-light text-white">
            ${candles[candles.length - 1].close.toFixed(2)}
          </div>
          <div className={`text-sm ${candles[candles.length - 1].isGreen ? 'text-green-400' : 'text-red-400'}`}>
            {candles[candles.length - 1].isGreen ? '▲' : '▼'} 
            {' '}
            {Math.abs(((candles[candles.length - 1].close - candles[candles.length - 1].open) / candles[candles.length - 1].open) * 100).toFixed(2)}%
          </div>
        </div>
      </div>
    </ChartWrapper>
  );
}