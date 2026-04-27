'use client';

import { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';

export default function NetworkGraph() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState({ nodes: [], edges: [] });

  useEffect(() => {
    fetch('http://localhost:8000/api/network/graph')
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (containerRef.current && data.nodes.length > 0) {
      new Network(containerRef.current, data, {
        nodes: { shape: 'dot', size: 16 },
        edges: { arrows: 'to' }
      });
    }
  }, [data]);

  return <div ref={containerRef} style={{ width: '100%', height: '600px' }} />;
}
