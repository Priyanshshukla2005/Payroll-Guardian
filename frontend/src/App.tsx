import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { UploadPayroll } from './pages/UploadPayroll';
import { Analysis } from './pages/Analysis';
import { AnomalyDetails } from './pages/AnomalyDetails';
import { Compliance } from './pages/Compliance';
import { Assistant } from './pages/Assistant';
import { LandingOverview } from './pages/LandingOverview';
import { NotFound } from './pages/NotFound';
import { AnalysisResponse, AuthUser } from './types/api';
import { DEMO_ANALYSIS } from './utils/sampleData';
import { payrollApi } from './services/payrollApi';
import { authApi } from './services/authApi';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(() => authApi.getCurrentUser());

  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResponse | null>(() => {
    const saved = localStorage.getItem('payroll_guardian_active_analysis');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return null;
      }
    }
    return null;
  });

  useEffect(() => {
    if (currentAnalysis) {
      localStorage.setItem('payroll_guardian_active_analysis', JSON.stringify(currentAnalysis));
    }
  }, [currentAnalysis]);

  // Synchronize canonical demo analysis from backend if no analysis is active
  useEffect(() => {
    if (!currentAnalysis || currentAnalysis.analysis_id === 'anl_demo_202406') {
      payrollApi
        .getAnalysis('anl_demo_202406')
        .then((data) => {
          if (data && data.analysis_id) {
            setCurrentAnalysis(data);
          }
        })
        .catch(() => {
          if (!currentAnalysis) {
            setCurrentAnalysis(DEMO_ANALYSIS);
          }
        });
    }
  }, []);

  const handleSetAnalysis = (analysis: AnalysisResponse) => {
    setCurrentAnalysis(analysis);
  };

  const handleLoadDemo = () => {
    payrollApi
      .getAnalysis('anl_demo_202406')
      .then((data) => {
        setCurrentAnalysis(data);
      })
      .catch(() => {
        setCurrentAnalysis(DEMO_ANALYSIS);
      });
  };

  const handleUserChange = (user: AuthUser) => {
    setCurrentUser(user);
  };

  return (
    <Router>
      <Layout
        activePeriod={currentAnalysis?.payroll_period || '2024-06'}
        analysisId={currentAnalysis?.analysis_id}
        currentUser={currentUser}
        onUserChange={handleUserChange}
      >
        <Routes>
          <Route
            path="/"
            element={
              <LandingOverview
                currentAnalysis={currentAnalysis}
                onLoadDemo={handleLoadDemo}
              />
            }
          />
          <Route
            path="/dashboard"
            element={
              <Dashboard
                currentAnalysis={currentAnalysis}
                onLoadDemo={handleLoadDemo}
              />
            }
          />
          <Route
            path="/payroll/upload"
            element={
              <UploadPayroll
                onAnalysisSuccess={handleSetAnalysis}
              />
            }
          />
          <Route
            path="/analysis"
            element={
              <Analysis
                currentAnalysis={currentAnalysis}
                onSetCurrentAnalysis={handleSetAnalysis}
              />
            }
          />
          <Route
            path="/analysis/:analysisId"
            element={
              <Analysis
                currentAnalysis={currentAnalysis}
                onSetCurrentAnalysis={handleSetAnalysis}
              />
            }
          />
          <Route
            path="/anomalies/:analysisId/:employeeId"
            element={<AnomalyDetails currentAnalysis={currentAnalysis} />}
          />
          <Route path="/compliance" element={<Compliance />} />
          <Route
            path="/assistant"
            element={<Assistant currentAnalysis={currentAnalysis} />}
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;
