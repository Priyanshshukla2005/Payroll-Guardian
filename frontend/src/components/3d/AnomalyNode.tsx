import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface AnomalyNodeData {
  radius: number;
  speed: number;
  offset: number;
  size: number;
  label: string;
}

const NODES: AnomalyNodeData[] = [
  { radius: 2.9, speed: 0.45, offset: 0, size: 0.12, label: 'RULE_PF_MISMATCH' },
  { radius: 3.3, speed: -0.35, offset: 2.1, size: 0.14, label: 'ATTENDANCE_OVERFLOW' },
  { radius: 3.1, speed: 0.55, offset: 4.2, size: 0.11, label: 'SALARY_OUTLIER' },
];

export const AnomalyNodes: React.FC = () => {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    if (!groupRef.current) return;

    groupRef.current.children.forEach((child, index) => {
      const node = NODES[index];
      if (!node) return;

      const angle = time * node.speed + node.offset;
      const x = Math.cos(angle) * node.radius;
      const z = Math.sin(angle) * node.radius;
      const y = Math.sin(time * 0.8 + node.offset) * 0.5;

      child.position.set(x, y, z);
    });
  });

  return (
    <group ref={groupRef}>
      {NODES.map((node, i) => (
        <group key={i}>
          {/* Pulsing Alert Orb */}
          <mesh>
            <sphereGeometry args={[node.size, 16, 16]} />
            <meshStandardMaterial
              color="#f43f5e"
              emissive="#fb7185"
              emissiveIntensity={1.8}
              roughness={0.2}
            />
          </mesh>
          {/* Subtle Halos */}
          <mesh>
            <sphereGeometry args={[node.size * 1.6, 16, 16]} />
            <meshBasicMaterial
              color="#f43f5e"
              wireframe
              transparent
              opacity={0.35}
            />
          </mesh>
        </group>
      ))}
    </group>
  );
};
