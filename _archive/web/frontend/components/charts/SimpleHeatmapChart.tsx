'use client';

import React from 'react';
import ChartWrapper from './ChartWrapper';

export default function SimpleHeatmapChart() {
  const tokens = ['BTC', 'ETH', 'BNB', 'SOL', 'MATIC', 'AVAX', 'DOT', 'LINK'];
  const timeframes = ['1H', '4H', '1D', '1W'];
  
  // Generate heatmap data (-100 to +100 representing percentage change)
  const data = tokens.map(token => 
    timeframes.map(() => (Math.random() - 0.5) * 20)
  );

  const getColor = (value: number) => {
    if (value > 10) return '#06ffa5';
    if (value > 5) return '#10b981';
    if (value > 0) return '#059669';
    if (value > -5) return '#dc2626';
    if (value > -10) return '#ef4444';
    return '#7f1d1d';
  };

  const getOpacity = (value: number) => {
    return 0.3 + (Math.abs(value) / 20) * 0.7;
  };

  return (
    <ChartWrapper height={350}>
      <div className="w-full h-full p-4">
        <div className="grid grid-cols-5 gap-2 h-full">
          {/* Token labels */}
          <div className="flex flex-col justify-between py-8">
            {tokens.map(token => (
              <div key={token} className="text-sm text-neutral-400 font-medium">
                {token}
              </div>
            ))}
          </div>
          
          {/* Heatmap grid */}
          <div className="col-span-4">
            {/* Timeframe labels */}
            <div className="grid grid-cols-4 gap-2 mb-2">
              {timeframes.map(tf => (
                <div key={tf} className="text-sm text-neutral-400 text-center font-medium">
                  {tf}
                </div>
              ))}
            </div>
            
            {/* Heatmap cells */}
            <div className="grid gap-2">
              {data.map((row, i) => (
                <div key={i} className="grid grid-cols-4 gap-2">
                  {row.map((value, j) => (
                    <div
                      key={j}
                      className="relative group cursor-pointer transition-all duration-200 hover:scale-105"
                      style={{
                        backgroundColor: getColor(value),
                        opacity: getOpacity(value),
                        aspectRatio: '1/1',
                        borderRadius: '8px',
                        boxShadow: value > 0 
                          ? `0 0 20px ${getColor(value)}40`
                          : 'none'
                      }}
                    >
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-xs font-medium text-white opacity-0 group-hover:opacity-100 transition-opacity">
                          {value > 0 ? '+' : ''}{value.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Legend */}
        <div className="mt-4 flex items-center justify-center gap-4">
          <span className="text-xs text-neutral-500">Strong Sell</span>
          <div className="flex gap-1">
            {[-15, -10, -5, 0, 5, 10, 15].map(v => (
              <div
                key={v}
                className="w-4 h-4 rounded"
                style={{
                  backgroundColor: getColor(v),
                  opacity: getOpacity(v)
                }}
              />
            ))}
          </div>
          <span className="text-xs text-neutral-500">Strong Buy</span>
        </div>
      </div>
    </ChartWrapper>
  );
}