import type { CSSProperties } from 'react';

export type GradientWavesDetail = 'low' | 'medium' | 'high';

export interface GradientWavesProps {
  horizonColor?: string;
  waveColor?: string;
  crestColor?: string;
  speed?: number;
  amplitude?: number;
  waveScale?: number;
  waveRatio?: number;
  swell?: number;
  turbulence?: number;
  tilt?: number;
  zoom?: number;
  height?: number;
  baseHeight?: number;
  fogDepth?: number;
  detail?: GradientWavesDetail;
  brightness?: number;
  opacity?: number;
  grain?: boolean;
  grainIntensity?: number;
  mouseInteraction?: boolean;
  mouseInfluence?: number;
  mouseSmoothing?: number;
  parallax?: boolean;
  parallaxStrength?: number;
  style?: CSSProperties;
  className?: string;
}

declare const GradientWaves: (props: GradientWavesProps) => JSX.Element;

export default GradientWaves;