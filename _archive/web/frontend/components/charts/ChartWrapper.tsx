'use client';

import React, { useEffect, useState } from 'react';

interface ChartWrapperProps {
  children: React.ReactNode;
  height?: number;
  loadingText?: string;
}

export default function ChartWrapper({ 
  children, 
  height = 400,
  loadingText = "Loading chart..."
}: ChartWrapperProps) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return (
      <div 
        className="flex items-center justify-center bg-white/[0.02] rounded-lg animate-pulse"
        style={{ height: `${height}px` }}
      >
        <span className="text-neutral-500 text-sm">{loadingText}</span>
      </div>
    );
  }

  return <>{children}</>;
}