'use client';

import { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';

interface Node {
  id: number | string;
  label: string;
  [key: string]: unknown;
}

interface Edge {
  from: number | string;
  to: number | string;
  [key: string]: unknown;
}

interface NetworkData {
  nodes: Node[];
  edges: Edge[];
}

export default function NetworkGraph() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<NetworkData>({ nodes: [], edges: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/network/graph`)
      .then((res) => {
        if (!res.ok) {
          throw new Error('Failed to fetch network graph data');
        }
        return res.json();
      })
      .then((json: NetworkData) => {
        setData(json);
        setError(null);
      })
      .catch((err) => {
        console.error(err);
        setError('Failed to load network graph data.');
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  useEffect(() => {
    if (containerRef.current && data.nodes.length > 0) {
      const network = new Network(containerRef.current, data, {
        nodes: { shape: 'dot', size: 16 },
        edges: { arrows: 'to' }
      });
      return () => network.destroy();
    }
  }, [data]);

  if (isLoading) {
    return <div className="flex items-center justify-center w-full h-[600px]">Loading network graph...</div>;
  }

  if (error) {
    return <div className="flex items-center justify-center w-full h-[600px] text-red-500">{error}</div>;
  }

  return <div ref={containerRef} style={{ width: '100%', height: '600px' }} />;
}
