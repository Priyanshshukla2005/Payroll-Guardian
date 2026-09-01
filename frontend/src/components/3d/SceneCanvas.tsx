import React, { Suspense, useEffect, useState, Component } from 'react';
import { Canvas } from '@react-three/fiber';

interface ErrorBoundaryProps {
  fallback: React.ReactNode;
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

class WebGLErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: any) {
    console.warn('WebGL 3D canvas failed to render, switching to fallback:', error);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

// Check for WebGL capability safely in browser
function detectWebGL(): boolean {
  try {
    const canvas = document.createElement('canvas');
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    );
  } catch {
    return false;
  }
}

interface SceneCanvasProps {
  children: React.ReactNode;
  className?: string;
  fallbackGraphic?: React.ReactNode;
}

export const SceneCanvas: React.FC<SceneCanvasProps> = ({
  children,
  className = 'w-full h-full min-h-[420px]',
  fallbackGraphic,
}) => {
  const [hasWebGL, setHasWebGL] = useState<boolean>(true);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(false);

  useEffect(() => {
    setHasWebGL(detectWebGL());
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  const defaultFallback = fallbackGraphic || (
    <div className="relative w-full h-full min-h-[420px] flex items-center justify-center bg-obsidian-900/60 border border-white/5 rounded-2xl overflow-hidden p-8">
      <div className="absolute inset-0 bg-radial-gradient pointer-events-none" />
      <div className="relative flex flex-col items-center text-center">
        {/* Abstract animated SVG Core */}
        <div className="relative w-48 h-48 mb-6">
          <div className="absolute inset-0 rounded-full border border-cyan-500/30 animate-spin-slow" />
          <div className="absolute inset-4 rounded-full border border-dashed border-indigo-500/40 animate-spin" style={{ animationDirection: 'reverse', animationDuration: '25s' }} />
          <div className="absolute inset-8 rounded-full border border-cyan-400/20 animate-pulse-slow" />
          <div className="absolute inset-16 rounded-full bg-cyan-500/20 blur-xl animate-pulse" />
          <div className="absolute inset-20 rounded-full bg-cyan-400/80 shadow-[0_0_30px_#00f0ff]" />
        </div>
        <span className="font-mono text-xs uppercase tracking-widest text-cyan-400 font-semibold mb-1">
          AI Payroll Intelligence Core
        </span>
        <p className="text-xs text-slate-400 max-w-xs">
          Neural network verifying statutory bounds across EPFO, ESIC, TDS & Behavioral Cohorts.
        </p>
      </div>
    </div>
  );

  if (!hasWebGL || prefersReducedMotion) {
    return <div className={className}>{defaultFallback}</div>;
  }

  return (
    <div className={`relative ${className}`}>
      <WebGLErrorBoundary fallback={defaultFallback}>
        <Suspense fallback={defaultFallback}>
          <Canvas
            camera={{ position: [0, 0, 7.5], fov: 45 }}
            gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
            dpr={[1, 2]}
            style={{ pointerEvents: 'auto' }}
          >
            <ambientLight intensity={0.7} />
            <directionalLight position={[10, 10, 5]} intensity={1.2} color="#00f0ff" />
            <pointLight position={[-10, -10, -5]} intensity={0.8} color="#6366f1" />
            {children}
          </Canvas>
        </Suspense>
      </WebGLErrorBoundary>
    </div>
  );
};
