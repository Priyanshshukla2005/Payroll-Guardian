import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export const PayrollCore: React.FC = () => {
  const outerRef = useRef<THREE.Mesh>(null);
  const innerRef = useRef<THREE.Mesh>(null);
  const coreRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    const pointer = state.pointer;

    // Smooth idle rotation + mouse parallax tilt
    if (outerRef.current) {
      outerRef.current.rotation.x = time * 0.15 + pointer.y * 0.2;
      outerRef.current.rotation.y = time * 0.22 + pointer.x * 0.25;
    }

    if (innerRef.current) {
      innerRef.current.rotation.x = -time * 0.2 - pointer.y * 0.15;
      innerRef.current.rotation.y = -time * 0.3 - pointer.x * 0.2;
    }

    if (ringRef.current) {
      ringRef.current.rotation.z = time * 0.1;
      ringRef.current.rotation.x = Math.PI / 3 + Math.sin(time * 0.5) * 0.1;
    }

    // Organic core pulsation
    if (coreRef.current) {
      const pulse = 1 + Math.sin(time * 2.5) * 0.08;
      coreRef.current.scale.set(pulse, pulse, pulse);
    }
  });

  return (
    <group>
      {/* Outer Polyhedral Geodesic Wireframe */}
      <mesh ref={outerRef}>
        <icosahedronGeometry args={[2.1, 1]} />
        <meshStandardMaterial
          color="#06b6d4"
          emissive="#00f0ff"
          emissiveIntensity={0.35}
          wireframe
          transparent
          opacity={0.65}
          roughness={0.2}
          metalness={0.8}
        />
      </mesh>

      {/* Inner Nested Geometric Cage */}
      <mesh ref={innerRef}>
        <dodecahedronGeometry args={[1.4, 0]} />
        <meshStandardMaterial
          color="#6366f1"
          emissive="#818cf8"
          emissiveIntensity={0.5}
          wireframe
          transparent
          opacity={0.8}
          roughness={0.1}
          metalness={0.9}
        />
      </mesh>

      {/* Pulsing Solid Nucleus */}
      <mesh ref={coreRef}>
        <sphereGeometry args={[0.75, 32, 32]} />
        <meshStandardMaterial
          color="#00f0ff"
          emissive="#06b6d4"
          emissiveIntensity={1.2}
          roughness={0.1}
          metalness={0.5}
        />
      </mesh>

      {/* Equatorial Gyroscopic Ring */}
      <mesh ref={ringRef}>
        <torusGeometry args={[2.8, 0.02, 16, 100]} />
        <meshStandardMaterial
          color="#38bdf8"
          emissive="#00f0ff"
          emissiveIntensity={0.6}
          transparent
          opacity={0.7}
        />
      </mesh>
    </group>
  );
};
