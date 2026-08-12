import type { CSSProperties } from 'react';

export interface FloatingLinesWavePosition {
  x?: number;
  y?: number;
  rotate?: number;
}

export interface FloatingLinesProps {
  linesGradient?: string[];
  enabledWaves?: Array<'top' | 'middle' | 'bottom'>;
  lineCount?: number | number[];
  lineDistance?: number | number[];
  topWavePosition?: FloatingLinesWavePosition;
  middleWavePosition?: FloatingLinesWavePosition;
  bottomWavePosition?: FloatingLinesWavePosition;
  animationSpeed?: number;
  interactive?: boolean;
  bendRadius?: number;
  bendStrength?: number;
  mouseDamping?: number;
  parallax?: boolean;
  parallaxStrength?: number;
  mixBlendMode?: CSSProperties['mixBlendMode'];
}

declare const FloatingLines: (props: FloatingLinesProps) => JSX.Element;

export default FloatingLines;
