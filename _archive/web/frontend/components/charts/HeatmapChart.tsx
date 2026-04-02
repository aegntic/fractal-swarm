'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { colors } from '@/lib/design-system';

const ApexChart = dynamic(() => import('react-apexcharts'), { ssr: false });

interface HeatmapData {
  name: string;
  data: {
    x: string;
    y: number;
  }[];
}

const tokens = ['BTC', 'ETH', 'SOL', 'MATIC', 'ARB', 'OP', 'AVAX', 'LINK'];
const timeframes = ['1H', '4H', '1D', '1W', '1M'];

// Generate mock performance data
const generateMockData = (): HeatmapData[] => {
  return tokens.map(token => ({
    name: token,
    data: timeframes.map(tf => ({
      x: tf,
      y: Math.floor(Math.random() * 200 - 100) / 10 // -10% to +10%
    }))
  }));
};

export default function HeatmapChart() {
  const [data, setData] = useState<HeatmapData[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Initial data
    setData(generateMockData());
    setIsLoading(false);

    // Update data every 30 seconds
    const interval = setInterval(() => {
      setData(generateMockData());
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const options = {
    chart: {
      type: 'heatmap' as const,
      height: 350,
      toolbar: {
        show: false,
      },
      background: 'transparent',
    },
    dataLabels: {
      enabled: true,
      style: {
        fontSize: '12px',
        fontWeight: 600,
      },
      formatter: (val: number) => `${val > 0 ? '+' : ''}${val}%`
    },
    colors: ["#FF4444"],
    plotOptions: {
      heatmap: {
        shadeIntensity: 0.5,
        radius: 4,
        useFillColorAsStroke: false,
        colorScale: {
          ranges: [
            {
              from: -10,
              to: -5,
              name: 'Strong Sell',
              color: '#ef4444'
            },
            {
              from: -5,
              to: -2,
              name: 'Sell',
              color: '#f97316'
            },
            {
              from: -2,
              to: 2,
              name: 'Neutral',
              color: '#6b7280'
            },
            {
              from: 2,
              to: 5,
              name: 'Buy',
              color: '#3b82f6'
            },
            {
              from: 5,
              to: 10,
              name: 'Strong Buy',
              color: colors.accent.teal
            }
          ]
        }
      }
    },
    xaxis: {
      type: 'category' as const,
      categories: timeframes,
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
        }
      }
    },
    grid: {
      show: false
    },
    tooltip: {
      theme: 'dark',
      custom: function({ series, seriesIndex, dataPointIndex, w }: any) {
        const value = series[seriesIndex][dataPointIndex];
        const token = w.globals.labels[seriesIndex];
        const timeframe = timeframes[dataPointIndex];
        
        return (
          '<div class="p-2">' +
          '<div class="font-semibold">' + token + ' - ' + timeframe + '</div>' +
          '<div class="mt-1">Performance: <span class="font-bold ' + 
          (value > 0 ? 'text-green-400' : 'text-red-400') + '">' +
          (value > 0 ? '+' : '') + value + '%</span></div>' +
          '</div>'
        );
      }
    }
  };

  const series = data;

  if (isLoading) {
    return (
      <div className="h-[350px] flex items-center justify-center">
        <div className="animate-pulse text-neutral-400">Loading market data...</div>
      </div>
    );
  }

  return (
    <div className="w-full h-full">
      <ApexChart
        options={options}
        series={series}
        type="heatmap"
        height={350}
      />
    </div>
  );
}