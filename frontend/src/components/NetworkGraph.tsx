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

function textOnlyTooltip(value: unknown): HTMLElement {
  const tooltip = document.createElement('div');
  tooltip.textContent = value == null ? '' : String(value);
  return tooltip;
}

function sanitizeGraphItem<T extends Node | Edge>(item: T): T {
  const sanitized = { ...item };

  if (Object.prototype.hasOwnProperty.call(item, 'title')) {
    sanitized.title = textOnlyTooltip(item.title);
  }

  return sanitized;
}

function sanitizeNetworkData(data: NetworkData): NetworkData {
  return {
    nodes: data.nodes.map(sanitizeGraphItem),
    edges: data.edges.map(sanitizeGraphItem),
  };
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
        setData(sanitizeNetworkData(json));
        setError(null);
      })
      .catch((err) => {
        console.error(err);
        setError('관계 그래프를 불러오지 못했습니다.');
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
    return <div role="status" aria-live="polite" className="flex h-full min-h-[520px] w-full items-center justify-center text-sm text-muted-foreground"><RefreshCw className="mr-2 size-4 animate-spin" aria-hidden="true" />관계 그래프를 불러오는 중입니다...</div>;
  }

  if (error) {
    return (
      <div role="alert" className="flex h-full min-h-[520px] w-full items-center justify-center p-6 text-center">
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
      <div className="flex h-full min-h-[520px] w-full items-center justify-center p-6 text-center text-sm text-muted-foreground">
        <div className="max-w-xs rounded-2xl border border-dashed bg-muted/30 p-5">
          <Share2 className="mx-auto mb-3 size-8 text-primary/60" aria-hidden="true" />
          <p className="font-medium text-foreground">아직 연결 데이터가 없습니다.</p>
          <p className="mt-1 text-xs">메일이 쌓이면 발신자와 스레드 관계가 여기에 표시됩니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-[520px] flex-col">
      <div className="border-b border-border bg-card/80 p-4">
        <h4 className="text-sm font-black text-foreground">관계 이해</h4>
        <p className="mt-1 text-xs text-muted-foreground">
          노드 {data.nodes.length}개와 연결 {data.edges.length}개가 선택한 스레드 맥락에 연결되어 있습니다.
        </p>
      </div>
      <div
        ref={containerRef}
        role="img"
        aria-label={`관계 그래프. 노드 ${data.nodes.length}개, 연결 ${data.edges.length}개가 표시됩니다.`}
        className="min-h-0 flex-1 bg-[radial-gradient(circle_at_center,rgb(37_99_255_/_0.08),transparent_32rem)]"
      />
    </div>
  );
}
