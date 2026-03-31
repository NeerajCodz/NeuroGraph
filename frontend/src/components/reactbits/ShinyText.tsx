import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

type ShinyTextProps = {
  text: ReactNode;
  disabled?: boolean;
  speed?: number;
  className?: string;
};

export const ShinyText = ({ text, disabled = false, speed = 3, className = '' }: ShinyTextProps) => {

  return (
    <motion.div
      className={`text-transparent bg-clip-text bg-gradient-to-r from-transparent via-white to-transparent bg-[length:200%_auto] ${className}`}
      style={{
           backgroundImage: 'linear-gradient(120deg, rgba(255, 255, 255, 0) 40%, rgba(255, 255, 255, 0.8) 50%, rgba(255, 255, 255, 0) 60%)',
           backgroundSize: '200% auto',
           backgroundPosition: '0 center'
      }}
      animate={{
        backgroundPosition: disabled ? '0 center' : ['200% center', '-200% center'],
      }}
      transition={{
        repeat: Infinity,
        duration: speed,
        ease: 'linear',
      }}
    >
      {text}
    </motion.div>
  );
};