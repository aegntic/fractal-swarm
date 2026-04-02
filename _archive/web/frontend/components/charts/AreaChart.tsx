'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { colors, gradients } from '@/lib/design-system';

const ApexChart = dynamic(() => import('react-apexcharts'), { ssr: false });

interface DataPoint {
  x: Date;
  y: number;
}

// Generate mock portfolio value data with upward trend
const generateMockData = (): DataPoint[] => {
  const data: DataPoint[] = [];
  const startValue = 100000;
  let currentValue = startValue;
  
  for (let i = 30; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    
    // Simulate growth with volatility
    const dailyReturn = (Math.random() * 0.04 - 0.01) + 0.002; // Slight upward bias
    currentValue = currentValue * (1 + dailyReturn);
    
    data.push({
      x: new Date(date),
      y: Math.round(currentValue)
    });
  }
  
  return data;
};

export default function AreaChart() {
  const [data, setData] = useState<DataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Initial data
    setData(generateMockData());
    setIsLoading(false);

    // Update data every 10 seconds
    const interval = setInterval(() => {
      setData(prevData => {
        const newData = [...prevData.slice(1)];
        const lastValue = prevData[prevData.length - 1].y;
        
        // Simulate real-time portfolio value changes
        const change = (Math.random() * 0.002 - 0.0005) + 0.0001;
        const newValue = lastValue * (1 + change);
        
        newData.push({
          x: new Date(),
          y: Math.round(newValue)
        });
        
        return newData;
      });
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const currentValue = data.length > 0 ? data[data.length - 1].y : 0;
  const startValue = data.length > 0 ? data[0].y : 0;
  const change = startValue > 0 ? ((currentValue - startValue) / startValue * 100).toFixed(2) : '0.00';
  const isPositive = currentValue >= startValue;

  const options = {
    chart: {
      type: 'area' as const,
      height: 350,
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
    dataLabels: {
      enabled: false
    },
    stroke: {
      curve: 'smooth' as const,
      width: 2,
      colors: [colors.accent.teal]
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.7,
        opacityTo: 0.1,
        stops: [0, 100],
        colorStops: [
          {
            offset: 0,
            color: colors.accent.teal,
            opacity: 0.7
          },
          {
            offset: 100,
            color: colors.accent.teal,
            opacity: 0.1
          }
        ]
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
      labels: {
        style: {
          colors: colors.neutral[400],
          fontSize: '12px',
        },
        formatter: (value: number) => `$${(value / 1000).toFixed(0)}k`
      },
      min: Math.min(...data.map(d => d.y)) * 0.98,
      max: Math.max(...data.map(d => d.y)) * 1.02,
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
      x: {
        format: 'dd MMM yyyy'
      },
      y: {
        formatter: (value: number) => `$${value.toLocaleString()}`
      }
    }
  };

  const series = [{
    name: 'Portfolio Value',
    data: data
  }];

  if (isLoading) {
    return (
      <div className="h-[350px] flex items-center justify-center">
        <div className="animate-pulse text-neutral-400">Loading portfolio data...</div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-4">
        <div className="flex items-baseline gap-3">
          <h3 className="text-3xl font-bold text-white">${currentValue.toLocaleString()}</h3>
          <span className={`text-lg font-semibold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
            {isPositive ? '+' : ''}{change}%
          </span>
        </div>
        <p className="text-sm text-neutral-400 mt-1">Total Portfolio Value</p>
      </div>
      <ApexChart
        options={options}
        series={series}
        type="area"
        height={350}
      />
    </div>
  );
}