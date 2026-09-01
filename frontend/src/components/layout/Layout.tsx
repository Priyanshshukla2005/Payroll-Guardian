import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
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
  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          activePeriod={activePeriod}
          analysisId={analysisId}
          currentUser={currentUser}
          onUserChange={onUserChange}
        />
        <main className="flex-1 p-8 max-w-7xl w-full mx-auto overflow-x-hidden">
          {children}
        </main>
      </div>
    </div>
  );
};
