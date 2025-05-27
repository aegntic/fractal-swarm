'use client';

import React from 'react';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';

export default function WinRateGauge() {
  const winRate = 78.4;
  const totalTrades = 342;
  const winTrades = Math.floor(totalTrades * (winRate / 100));
  
  return (
    <div className="flex flex-col items-center">
      <div className="w-32 h-32 mb-4">
        <CircularProgressbar
          value={winRate}
          text={`${winRate}%`}
          styles={buildStyles({
            pathColor: `rgba(52, 211, 153, ${winRate / 100})`,
            textColor: '#34d399',
            trailColor: 'rgba(255, 255, 255, 0.05)',
            backgroundColor: 'transparent',
            pathTransitionDuration: 1,
            textSize: '20px',
          })}
        />
      </div>
      
      <div className="text-center">
        <div className="text-lg font-semibold text-white">{winTrades}/{totalTrades}</div>
        <div className="text-sm text-gray-400">Wins/Total</div>
      </div>
      
      <div className="mt-4 grid grid-cols-2 gap-4 w-full">
        <div className="text-center p-2 rounded-lg bg-green-500/10">
          <div className="text-sm font-semibold text-green-400">{winTrades}</div>
          <div className="text-xs text-gray-400">Wins</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-red-500/10">
          <div className="text-sm font-semibold text-red-400">{totalTrades - winTrades}</div>
          <div className="text-xs text-gray-400">Losses</div>
        </div>
      </div>
    </div>
  );
}