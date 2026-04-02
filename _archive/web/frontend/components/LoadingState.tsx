'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { colors } from '@/lib/design-system';

export default function LoadingState() {
  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: colors.background.primary }}>
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="text-center"
      >
        <div className="relative w-24 h-24 mx-auto mb-6">
          <motion.div
            className="absolute inset-0 rounded-full border-4 border-primary-500/20"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          />
          <motion.div
            className="absolute inset-0 rounded-full border-4 border-transparent border-t-primary-500"
            animate={{ rotate: -360 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
          />
          <motion.div
            className="absolute inset-2 rounded-full border-4 border-transparent border-b-accent-teal"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          />
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">Initializing Trading System</h2>
        <p className="text-sm text-neutral-400">Connecting to quantum swarm network...</p>
      </motion.div>
    </div>
  );
}