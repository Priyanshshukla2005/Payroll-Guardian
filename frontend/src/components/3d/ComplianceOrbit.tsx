import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const ANCHORS = [
  { name: 'EPFO Sec 6', angle: 0, color: '#10b981' },
  { name: 'ESIC Sec 39', angle: Math.PI * 0.5, color: '#06b6d4' },
  { name: 'IT Sec 192', angle: Math.PI, color: '#818cf8' },
  { name: 'Policy Cap', angle: Math.PI * 1.5, color: '#38bdf8' },
];

export const ComplianceOrbit: React.FC = () => {
  const groupRef = useRef<THREE.Group>(null);
  const radius = 3.8;

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.05;
      groupRef.current.rotation.z += delta * 0.02;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Outer Regulatory Track Ring */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[radius, 0.015, 16, 120]} />
        <meshBasicMaterial color="#334155" transparent opacity={0.4} />
      </mesh>

      {/* Statutory Anchors */}
      {ANCHORS.map((anchor, i) => {
        const x = Math.cos(anchor.angle) * radius;
        const z = Math.sin(anchor.angle) * radius;

        return (
          <group key={i} position={[x, 0, z]}>
            <mesh>
              <octahedronGeometry args={[0.13, 0]} />
              <meshStandardMaterial
                color={anchor.color}
                emissive={anchor.color}
                emissiveIntensity={1.2}
                metalness={0.8}
                roughness={0.2}
              />
            </mesh>
            <mesh>
              <octahedronGeometry args={[0.22, 0]} />
              <meshBasicMaterial
                color={anchor.color}
                wireframe
                transparent
                opacity={0.25}
              />
            </mesh>
          </group>
        );
      })}
    </group>
  );
};
