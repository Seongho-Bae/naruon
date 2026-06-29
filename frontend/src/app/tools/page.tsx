"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { DashboardLayout } from "@/components/DashboardLayout";

interface ToolInfo {
  name: string;
  description: string;
  category: string;
}

export default function ToolsPage() {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    apiClient.get<ToolInfo[]>("/api/tools")
      .then((data) => {
        if (isMounted) {
          setTools(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) setLoading(false);
      });
    return () => { isMounted = false; };
  }, []);

  return (
    <DashboardLayout>
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">도구 목록</h1>
          <p className="text-sm text-slate-500 mt-2">이 AI 워크스페이스에서 자동화 분석 및 작업 실행에 사용하는 도구 목록입니다.</p>
        </header>

        {loading ? (
          <div role="status" aria-live="polite" className="text-sm text-slate-500">
            도구 목록을 불러오는 중입니다...
          </div>
        ) : tools.length === 0 ? (
          <div role="status" aria-live="polite" className="text-sm text-slate-500 bg-slate-50 p-6 rounded-xl border border-slate-200/60 text-center">
            사용 가능한 도구가 없습니다.
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {tools.map((tool, idx) => (
              <div key={idx} className="bg-white p-6 rounded-xl border border-slate-200/60 shadow-sm transition-shadow hover:shadow-md flex flex-col h-full">
                <div className="mb-4">
                  <span className="inline-block px-2.5 py-1 bg-indigo-50 text-indigo-700 text-xs font-medium rounded-full mb-3">
                    {tool.category}
                  </span>
                  <h3 className="font-medium text-slate-900">{tool.name}</h3>
                </div>
                <p className="text-sm text-slate-500 leading-relaxed flex-grow">{tool.description}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
