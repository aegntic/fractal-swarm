'use client';

import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export default function VolumeChart() {
  const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`);
  const volumes = hours.map(() => Math.floor(Math.random() * 50000) + 10000);

  const data = {
    labels: hours,
    datasets: [
      {
        label: 'Volume',
        data: volumes,
        backgroundColor: volumes.map(v => 
          v > 40000 ? 'rgba(52, 211, 153, 0.6)' : 
          v > 25000 ? 'rgba(96, 165, 250, 0.6)' : 
          'rgba(167, 139, 250, 0.6)'
        ),
        borderColor: volumes.map(v => 
          v > 40000 ? 'rgba(52, 211, 153, 1)' : 
          v > 25000 ? 'rgba(96, 165, 250, 1)' : 
          'rgba(167, 139, 250, 1)'
        ),
        borderWidth: 1,
        borderRadius: 4,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(96, 165, 250, 0.5)',
        borderWidth: 1,
        padding: 12,
        displayColors: false,
        callbacks: {
          label: (context: any) => {
            return `$${context.parsed.y.toLocaleString()}`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          display: false,
          drawBorder: false
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.5)',
          font: {
            size: 9
          },
          maxRotation: 0,
          callback: function(value: any, index: number) {
            return index % 4 === 0 ? hours[index] : '';
          }
        }
      },
      y: {
        grid: {
          color: 'rgba(255, 255, 255, 0.03)',
          drawBorder: false
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.5)',
          font: {
            size: 10
          },
          callback: function(value: any) {
            return '$' + (value / 1000) + 'k';
          }
        }
      }
    }
  };

  return (
    <div className="h-48">
      <Bar data={data} options={options} />
    </div>
  );
}