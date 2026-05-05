'use client';

import { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';
import { RefreshCw, Share2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

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

  const loadGraph = () => {
    setIsLoading(true);
    setError(null);
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
  };

  useEffect(() => {
    void Promise.resolve().then(loadGraph);
  }, []);

  useEffect(() => {
    if (containerRef.current && data.nodes.length > 0) {
      const network = new Network(containerRef.current, data, {
        nodes: {
          shape: 'dot',
          size: 16,
          color: {
            background: '#2563EB',
            border: '#0B132B',
            highlight: { background: '#7C3AED', border: '#4F46E5' }
          },
          font: { color: '#0B132B', face: 'Pretendard, system-ui, sans-serif' }
        },
        edges: { arrows: 'to', color: { color: '#CBD5E1', highlight: '#2563EB' }, smooth: true },
        physics: { stabilization: true }
      });
      return () => network.destroy();
    }
  }, [data]);

  if (isLoading) {
    return <div className="flex h-full min-h-[420px] items-center justify-center text-sm text-muted-foreground"><RefreshCw className="mr-2 size-4 animate-spin" aria-hidden="true" />관계 그래프를 불러오는 중입니다...</div>;
  }

  if (error) {
    return (
      <div className="flex h-full min-h-[420px] items-center justify-center p-6 text-center">
        <div className="max-w-xs rounded-2xl border border-destructive/20 bg-destructive/5 p-5 text-sm text-destructive">
          <Share2 className="mx-auto mb-3 size-8" aria-hidden="true" />
          <p className="font-medium">관계 그래프를 불러오지 못했습니다.</p>
          <p className="mt-1 text-xs text-destructive/80">API 서버 연결을 확인한 뒤 다시 시도하세요.</p>
          <Button className="mt-3" type="button" variant="outline" size="sm" onClick={loadGraph}>다시 시도</Button>
        </div>
      </div>
    );
  }

  if (data.nodes.length === 0) {
    return (
      <div className="flex h-full min-h-[420px] items-center justify-center p-6 text-center text-sm text-muted-foreground">
        <div className="max-w-xs rounded-2xl border border-dashed bg-muted/30 p-5">
          <Share2 className="mx-auto mb-3 size-8 text-primary/60" aria-hidden="true" />
          <p className="font-medium text-foreground">아직 연결 데이터가 없습니다.</p>
          <p className="mt-1 text-xs">메일이 쌓이면 발신자와 스레드 관계가 여기에 표시됩니다.</p>
        </div>
      </div>
    );
  }

  return <div ref={containerRef} className="h-full min-h-[420px] w-full" role="img" aria-label={`관계 그래프. 노드 ${data.nodes.length}개, 연결 ${data.edges.length}개가 표시됩니다.`} />;
}
