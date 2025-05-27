import { MaterialNode } from '@react-three/fiber';
import { LineDashedMaterial } from 'three';

declare module '@react-three/fiber' {
  interface ThreeElements {
    lineDashedMaterial: MaterialNode<LineDashedMaterial, typeof LineDashedMaterial>;
  }
}