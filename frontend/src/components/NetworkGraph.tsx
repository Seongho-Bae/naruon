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

import { apiClient } from '@/lib/api-client';

export default function NetworkGraph() {
  const containerRef = useRef<HTMLDivElement>(null);

  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient.get<NetworkData>('/api/network/graph')
      .then((data) => {
        setNodes(data.nodes);
        setEdges(data.edges);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load network graph:', err);
        setError('Failed to load network relationships');
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (containerRef.current && nodes.length > 0) {
      const network = new Network(containerRef.current, { nodes, edges }, {
        nodes: { shape: 'dot', size: 16 },
        edges: { arrows: 'to' }
      });
      return () => network.destroy();
    }
  }, [nodes, edges]);

  if (loading) {
    return <div role="status" aria-live="polite" className="flex h-full min-h-[520px] w-full items-center justify-center text-sm text-muted-foreground">관계 그래프를 불러오는 중입니다...</div>;
  }

  if (error) {
    return <div role="alert" className="flex h-full min-h-[520px] w-full items-center justify-center p-6 text-center text-sm text-red-500">관계 그래프를 불러오지 못했습니다.</div>;
  }

  if (nodes.length === 0) {
    return (
      <div className="flex h-full min-h-[520px] w-full items-center justify-center p-6 text-center">
        <div className="max-w-xs rounded-2xl border border-primary/15 bg-primary/5 p-5">
          <div className="mx-auto mb-3 grid size-12 place-items-center rounded-2xl bg-primary/10 text-2xl" aria-hidden="true">✦</div>
          <h4 className="font-bold text-foreground">관계 데이터가 없습니다</h4>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">메일이 연결되면 사람, 주제, 일정의 흐름을 그래프로 보여줍니다.</p>
        </div>
      </div>
    );
  }

  const nodeLabels = nodes
    .map((node) => String(node.label ?? node.id))
    .filter(Boolean)
    .slice(0, 5);

  return (
    <div className="flex h-full min-h-[520px] flex-col">
      <div className="border-b border-border bg-card/80 p-4">
        <h4 className="text-sm font-black text-foreground">관계 이해</h4>
        <p className="mt-1 text-xs text-muted-foreground">
          {nodes.length}개 노드와 {edges.length}개 관계가 이 스레드 맥락에 연결되어 있습니다.
        </p>
        <div className="mt-3 rounded-xl border border-primary/10 bg-primary/5 p-3 text-xs text-muted-foreground">
          <p className="font-semibold text-foreground">텍스트 관계 요약</p>
          <p className="mt-1">
            관련 노드: {nodeLabels.join(', ')}
          </p>
        </div>
      </div>
      <div
        ref={containerRef}
        aria-label={`${nodes.length}개 노드와 ${edges.length}개 관계가 있는 네트워크 그래프`}
        className="min-h-0 flex-1 bg-[radial-gradient(circle_at_center,rgb(37_99_255_/_0.08),transparent_32rem)]"
      />
    </div>
  );
}
