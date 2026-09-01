import React from 'react';
import { PayrollCore } from './PayrollCore';
import { DataParticles } from './DataParticles';
import { AnomalyNodes } from './AnomalyNode';
import { ComplianceOrbit } from './ComplianceOrbit';

export const IntelligenceNetwork: React.FC = () => {
  return (
    <group position={[0, 0, 0]}>
      {/* Central Intelligence Polyhedron */}
      <PayrollCore />

      {/* Orbiting Streaming Data Particles */}
      <DataParticles count={150} />

      {/* Detected Anomaly Risk Satellites */}
      <AnomalyNodes />

      {/* Outer Statutory Orbit Anchors */}
      <ComplianceOrbit />
    </group>
  );
};
