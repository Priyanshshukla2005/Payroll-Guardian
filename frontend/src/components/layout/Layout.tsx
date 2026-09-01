import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import Lenis from 'lenis';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Footer } from './Footer';
import { AuthUser } from '../../types/api';

interface Props {
  children: React.ReactNode;
  activePeriod?: string;
  analysisId?: string;
  currentUser: AuthUser | null;
  onUserChange: (user: AuthUser) => void;
}

export const Layout: React.FC<Props> = ({
  children,
  activePeriod,
  analysisId,
  currentUser,
  onUserChange,
}) => {
  const location = useLocation();
  const isLandingPage = location.pathname === '/';

  // Initialize Lenis smooth scroll for fluid physics
  useEffect(() => {
    // Respect user's preference for reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const lenis = new Lenis({
      duration: 1.1,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });

    let rafId: number;
    function raf(time: number) {
      lenis.raf(time);
      rafId = requestAnimationFrame(raf);
    }
    rafId = requestAnimationFrame(raf);

    return () => {
      cancelAnimationFrame(rafId);
      lenis.destroy();
    };
  }, [location.pathname]);

  if (isLandingPage) {
    return (
      <div className="min-h-screen bg-obsidian-950 text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-black">
        <Header
          activePeriod={activePeriod}
          analysisId={analysisId}
          currentUser={currentUser}
          onUserChange={onUserChange}
        />
        <main className="flex-1 w-full overflow-x-hidden">
          {children}
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-obsidian-950 text-slate-100 selection:bg-cyan-500 selection:text-black">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          activePeriod={activePeriod}
          analysisId={analysisId}
          currentUser={currentUser}
          onUserChange={onUserChange}
        />
        <main className="flex-1 p-6 lg:p-8 max-w-7xl w-full mx-auto overflow-x-hidden">
          {children}
        </main>
        <Footer />
      </div>
    </div>
  );
};
