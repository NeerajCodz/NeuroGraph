// Type declarations for JSX components without TypeScript definitions

declare module '@/components/text/ScrollFloat' {
  const ScrollFloat: React.FC<{
    children?: React.ReactNode;
    [key: string]: unknown;
  }>;
  export default ScrollFloat;
}

declare module '@/components/ScrollStack' {
  const ScrollStack: React.FC<{
    children?: React.ReactNode;
    className?: string;
    itemDistance?: number;
    itemScale?: number;
    itemStackDistance?: number;
    stackPosition?: string;
    scaleEndPosition?: string;
    baseScale?: number;
    scaleDuration?: number;
    rotationAmount?: number;
    blurAmount?: number;
    useWindowScroll?: boolean;
    onStackComplete?: () => void;
    [key: string]: unknown;
  }>;
  export default ScrollStack;
  export const ScrollStackItem: React.FC<{
    children?: React.ReactNode;
    itemClassName?: string;
    [key: string]: unknown;
  }>;
}

declare module '@/components/landing/Silk' {
  const Silk: React.FC<{
    [key: string]: unknown;
  }>;
  export default Silk;
}

declare module '@/components/landing/GridMotion' {
  const GridMotion: React.FC<{
    [key: string]: unknown;
  }>;
  export default GridMotion;
}

declare module '@/components/landing/Plasma' {
  const Plasma: React.FC<{
    [key: string]: unknown;
  }>;
  export default Plasma;
}

declare module '@/components/landing/LiquidEther' {
  const LiquidEther: React.FC<{
    colors?: string[];
    mouseForce?: number;
    cursorSize?: number;
    isViscous?: boolean;
    viscous?: number;
    iterationsViscous?: number;
    iterationsPoisson?: number;
    resolution?: number;
    isBounce?: boolean;
    autoDemo?: boolean;
    autoSpeed?: number;
    autoIntensity?: number;
    takeoverDuration?: number;
    autoResumeDelay?: number;
    autoRampDuration?: number;
    color0?: string;
    color1?: string;
    color2?: string;
    [key: string]: unknown;
  }>;
  export default LiquidEther;
}
