'use client';

import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function CloneDistribution() {
  const data = {
    labels: ['Gen 0', 'Gen 1', 'Gen 2', 'Gen 3+'],
    datasets: [
      {
        data: [12, 8, 5, 2],
        backgroundColor: [
          'rgba(96, 165, 250, 0.8)',
          'rgba(167, 139, 250, 0.8)',
          'rgba(244, 114, 182, 0.8)',
          'rgba(52, 211, 153, 0.8)',
        ],
        borderColor: [
          'rgba(96, 165, 250, 1)',
          'rgba(167, 139, 250, 1)',
          'rgba(244, 114, 182, 1)',
          'rgba(52, 211, 153, 1)',
        ],
        borderWidth: 2,
        hoverOffset: 4,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: 'rgba(255, 255, 255, 0.7)',
          padding: 12,
          font: {
            size: 11
          },
          usePointStyle: true,
          pointStyle: 'circle'
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(96, 165, 250, 0.5)',
        borderWidth: 1,
        padding: 12,
        displayColors: true,
        callbacks: {
          label: (context: any) => {
            const label = context.label || '';
            const value = context.parsed || 0;
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: ${value} (${percentage}%)`;
          }
        }
      }
    },
    cutout: '60%',
  };

  return (
    <div className="h-48 flex items-center justify-center">
      <Doughnut data={data} options={options} />
    </div>
  );
}