'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { colors } from '@/lib/design-system';

const ApexChart = dynamic(() => import('react-apexcharts'), { ssr: false });

interface SparklineChartProps {
  data: number[];
  color?: string;
  height?: number;
  showTooltip?: boolean;
}

export default function SparklineChart({ 
  data, 
  color = colors.accent.teal, 
  height = 40,
  showTooltip = false 
}: SparklineChartProps) {
  const isPositive = data.length > 1 && data[data.length - 1] > data[0];
  
  const options = {
    chart: {
      type: 'line' as const,
      sparkline: {
        enabled: true
      },
      animations: {
        enabled: true,
        easing: 'linear',
        dynamicAnimation: {
          speed: 1000
        }
      }
    },
    stroke: {
      curve: 'smooth' as const,
      width: 2,
      colors: [isPositive ? colors.success : colors.error]
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.4,
        opacityTo: 0.1,
        stops: [0, 100],
        colorStops: [
          {
            offset: 0,
            color: isPositive ? colors.success : colors.error,
            opacity: 0.4
          },
          {
            offset: 100,
            color: isPositive ? colors.success : colors.error,
            opacity: 0.1
          }
        ]
      }
    },
    tooltip: {
      enabled: showTooltip,
      theme: 'dark',
      x: {
        show: false
      },
      y: {
        title: {
          formatter: () => ''
        },
        formatter: (value: number) => `$${value.toFixed(2)}`
      }
    }
  };

  const series = [{
    name: 'Value',
    data: data
  }];

  return (
    <ApexChart
      options={options}
      series={series}
      type="area"
      height={height}
      width="100%"
    />
  );
}