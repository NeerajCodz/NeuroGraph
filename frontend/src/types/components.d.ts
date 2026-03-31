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

declare module '@/components/landing/Hyperspeed' {
  interface HyperspeedEffectOptions {
    onSpeedUp?: () => void;
    onSlowDown?: () => void;
    distortion?: string;
    length?: number;
    roadWidth?: number;
    islandWidth?: number;
    lanesPerRoad?: number;
    fov?: number;
    fovSpeedUp?: number;
    speedUp?: number;
    carLightsFade?: number;
    totalSideLightSticks?: number;
    lightPairsPerRoadWay?: number;
    shoulderLinesWidthPercentage?: number;
    brokenLinesWidthPercentage?: number;
    brokenLinesLengthPercentage?: number;
    lightStickWidth?: [number, number];
    lightStickHeight?: [number, number];
    movingAwaySpeed?: [number, number];
    movingCloserSpeed?: [number, number];
    carLightsLength?: [number, number];
    carLightsRadius?: [number, number];
    carWidthPercentage?: [number, number];
    carShiftX?: [number, number];
    carFloorSeparation?: [number, number];
    colors?: {
      roadColor?: number;
      islandColor?: number;
      background?: number;
      shoulderLines?: number;
      brokenLines?: number;
      leftCars?: number[];
      rightCars?: number[];
      sticks?: number;
    };
  }
  const Hyperspeed: React.FC<{
    effectOptions?: HyperspeedEffectOptions;
  }>;
  export default Hyperspeed;
}
