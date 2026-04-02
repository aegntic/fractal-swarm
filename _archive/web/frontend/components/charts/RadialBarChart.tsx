'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { colors } from '@/lib/design-system';

const ApexChart = dynamic(() => import('react-apexcharts'), { ssr: false });

interface MetricData {
  name: string;
  value: number;
  color: string;
}

// Generate mock performance metrics
const generateMockData = (): MetricData[] => {
  return [
    {
      name: 'Win Rate',
      value: Math.floor(Math.random() * 20 + 70), // 70-90%
      color: colors.accent.teal
    },
    {
      name: 'Risk Score',
      value: Math.floor(Math.random() * 30 + 20), // 20-50%
      color: colors.accent.purple
    },
    {
      name: 'Efficiency',
      value: Math.floor(Math.random() * 15 + 80), // 80-95%
      color: colors.accent.orange
    },
    {
      name: 'Utilization',
      value: Math.floor(Math.random() * 25 + 65), // 65-90%
      color: colors.primary[500]
    }
  ];
};

export default function RadialBarChart() {
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Initial data
    setMetrics(generateMockData());
    setIsLoading(false);

    // Update data every 15 seconds
    const interval = setInterval(() => {
      setMetrics(generateMockData());
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  const options = {
    chart: {
      type: 'radialBar' as const,
      height: 380,
      background: 'transparent',
    },
    plotOptions: {
      radialBar: {
        offsetY: 0,
        startAngle: 0,
        endAngle: 270,
        hollow: {
          margin: 5,
          size: '30%',
          background: 'transparent',
          image: undefined,
        },
        track: {
          background: colors.neutral[800],
          strokeWidth: '100%',
          margin: 5,
        },
        dataLabels: {
          name: {
            show: true,
            fontSize: '14px',
            color: colors.neutral[400],
            offsetY: -5
          },
          value: {
            show: true,
            fontSize: '20px',
            color: colors.neutral[100],
            offsetY: 5,
            formatter: (val: number) => val + '%'
          },
          total: {
            show: true,
            label: 'Overall',
            color: colors.neutral[400],
            fontSize: '14px',
            formatter: function (w: any) {
              const avg = Math.round(
                w.globals.seriesTotals.reduce((a: number, b: number) => a + b, 0) / 
                w.globals.seriesTotals.length
              );
              return avg + '%';
            }
          }
        }
      }
    },
    colors: metrics.map(m => m.color),
    labels: metrics.map(m => m.name),
    stroke: {
      lineCap: 'round' as const
    },
    fill: {
      type: 'gradient',
      gradient: {
        shade: 'dark',
        type: 'vertical',
        shadeIntensity: 0.5,
        gradientToColors: metrics.map(m => m.color),
        inverseColors: false,
        opacityFrom: 1,
        opacityTo: 0.8,
        stops: [0, 100]
      }
    },
    grid: {
      show: false
    },
    legend: {
      show: true,
      floating: true,
      fontSize: '12px',
      position: 'left' as const,
      offsetX: 0,
      offsetY: 15,
      labels: {
        useSeriesColors: true,
      },
      markers: {
        size: 0
      },
      formatter: function(seriesName: string, opts: any) {
        return seriesName + ":  " + opts.w.globals.series[opts.seriesIndex] + "%";
      },
      itemMargin: {
        vertical: 3
      }
    },
    responsive: [{
      breakpoint: 480,
      options: {
        legend: {
          show: false
        }
      }
    }]
  };

  const series = metrics.map(m => m.value);

  if (isLoading) {
    return (
      <div className="h-[380px] flex items-center justify-center">
        <div className="animate-pulse text-neutral-400">Loading metrics...</div>
      </div>
    );
  }

  return (
    <div className="w-full h-full">
      <ApexChart
        options={options}
        series={series}
        type="radialBar"
        height={380}
      />
    </div>
  );
}