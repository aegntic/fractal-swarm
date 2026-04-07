'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { colors } from '@/lib/design-system';

const ApexChart = dynamic(() => import('react-apexcharts'), { ssr: false });

interface CandleData {
  x: Date;
  y: [number, number, number, number]; // [open, high, low, close]
}

// Generate mock candlestick data
const generateMockData = (): CandleData[] => {
  const data: CandleData[] = [];
  const basePrice = 45000;
  let lastClose = basePrice;
  
  for (let i = 90; i >= 0; i--) {
    const date = new Date();
    date.setHours(date.getHours() - i);
    
    const volatility = 0.02;
    const trend = Math.random() > 0.5 ? 1 : -1;
    
    const open = lastClose;
    const close = open * (1 + (Math.random() * volatility - volatility/2) * trend);
    const high = Math.max(open, close) * (1 + Math.random() * volatility/2);
    const low = Math.min(open, close) * (1 - Math.random() * volatility/2);
    
    data.push({
      x: new Date(date),
      y: [open, high, low, close]
    });
    
    lastClose = close;
  }
  
  return data;
};

export default function CandlestickChart() {
  const [data, setData] = useState<CandleData[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Initial data
    setData(generateMockData());
    setIsLoading(false);

    // Update data every 5 seconds for real-time effect
    const interval = setInterval(() => {
      setData(prevData => {
        const newData = [...prevData.slice(1)];
        const lastCandle = prevData[prevData.length - 1];
        const lastClose = lastCandle.y[3];
        
        const volatility = 0.02;
        const trend = Math.random() > 0.5 ? 1 : -1;
        
        const open = lastClose;
        const close = open * (1 + (Math.random() * volatility - volatility/2) * trend);
        const high = Math.max(open, close) * (1 + Math.random() * volatility/2);
        const low = Math.min(open, close) * (1 - Math.random() * volatility/2);
        
        newData.push({
          x: new Date(),
          y: [open, high, low, close]
        });
        
        return newData;
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const options = {
    chart: {
      type: 'candlestick' as const,
      height: 400,
      toolbar: {
        show: false,
      },
      background: 'transparent',
      animations: {
        enabled: true,
        easing: 'linear',
        dynamicAnimation: {
          speed: 1000
        }
      }
    },
    plotOptions: {
      candlestick: {
        colors: {
          upward: colors.accent.teal,
          downward: colors.error
        },
        wick: {
          useFillColor: true
        }
      }
    },
    xaxis: {
      type: 'datetime' as const,
      labels: {
        style: {
          colors: colors.neutral[400],
          fontSize: '12px',
        }
      },
      axisBorder: {
        show: false
      },
      axisTicks: {
        show: false
      }
    },
    yaxis: {
      tooltip: {
        enabled: true
      },
      labels: {
        style: {
          colors: colors.neutral[400],
          fontSize: '12px',
        },
        formatter: (value: number) => `$${value.toFixed(0)}`
      }
    },
    grid: {
      borderColor: colors.neutral[800],
      strokeDashArray: 0,
      xaxis: {
        lines: {
          show: false
        }
      },
      yaxis: {
        lines: {
          show: true
        }
      }
    },
    tooltip: {
      theme: 'dark',
      custom: function({ seriesIndex, dataPointIndex, w }: any) {
        const o = w.globals.seriesCandleO[seriesIndex][dataPointIndex];
        const h = w.globals.seriesCandleH[seriesIndex][dataPointIndex];
        const l = w.globals.seriesCandleL[seriesIndex][dataPointIndex];
        const c = w.globals.seriesCandleC[seriesIndex][dataPointIndex];
        
        return (
          '<div class="apexcharts-tooltip-candlestick">' +
          '<div>Open: <span class="value">$' + o.toFixed(2) + '</span></div>' +
          '<div>High: <span class="value">$' + h.toFixed(2) + '</span></div>' +
          '<div>Low: <span class="value">$' + l.toFixed(2) + '</span></div>' +
          '<div>Close: <span class="value">$' + c.toFixed(2) + '</span></div>' +
          '</div>'
        );
      }
    }
  };

  const series = [{
    name: 'Price',
    data: data
  }];

  if (isLoading) {
    return (
      <div className="h-[400px] flex items-center justify-center">
        <div className="animate-pulse text-neutral-400">Loading chart data...</div>
      </div>
    );
  }

  return (
    <div className="w-full h-full">
      <ApexChart
        options={options}
        series={series}
        type="candlestick"
        height={400}
      />
    </div>
  );
}