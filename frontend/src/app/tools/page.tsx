"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Loader2 } from "lucide-react";

interface ToolInfo {
  code: string;
  name: string;
  description: string;
  category: string;
  parameters?: Record<string, unknown>;
  is_active?: boolean;
}

interface ExecuteResponse {
  status: string;
  result: unknown;
  message?: string;
}

function buildDefaultParameters(tool: ToolInfo) {
  return Object.fromEntries(
    Object.entries(tool.parameters ?? {}).map(([key, descriptor]) => [
      key,
      defaultParameterValue(descriptor),
    ]),
  );
}

function defaultParameterValue(descriptor: unknown) {
  const type =
    typeof descriptor === "string"
      ? descriptor
      : descriptor && typeof descriptor === "object" && "type" in descriptor
        ? String((descriptor as { type?: unknown }).type)
        : "string";
  switch (type.toLowerCase()) {
    case "number":
    case "integer":
      return 0;
    case "boolean":
      return false;
    case "array":
      return [];
    case "object":
      return {};
    default:
      return "test_value";
  }
}

export default function ToolsPage() {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [executing, setExecuting] = useState<Record<string, boolean>>({});
  const [results, setResults] = useState<Record<string, ExecuteResponse>>({});

  useEffect(() => {
    let isMounted = true;
    apiClient.get<ToolInfo[]>("/api/tools")
      .then((data) => {
        if (isMounted) {
          setTools(data);
          setLoadError(false);
          setLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) {
          setLoadError(true);
          setLoading(false);
        }
      });
    return () => { isMounted = false; };
  }, []);

  const handleExecute = async (code: string) => {
    setExecuting(prev => ({ ...prev, [code]: true }));
    try {
      const tool = tools.find((item) => item.code === code);
      const params = tool ? buildDefaultParameters(tool) : {};
      const response = await apiClient.post<ExecuteResponse>(`/api/tools/${code}/execute`, { parameters: params });
      setResults(prev => ({ ...prev, [code]: response }));
    } catch (error: unknown) {
      const err = error as { message?: string };
      setResults(prev => ({
        ...prev,
        [code]: { status: "failed", result: null, message: err.message || "실행 중 오류가 발생했습니다." }
      }));
    } finally {
      setExecuting(prev => ({ ...prev, [code]: false }));
    }
  };

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
            {loadError ? "도구 목록을 불러오지 못했습니다. 잠시 후 다시 시도하세요." : "사용 가능한 도구가 없습니다."}
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {tools.map((tool) => (
              <div key={tool.code} className="bg-white p-6 rounded-xl border border-slate-200/60 shadow-sm transition-shadow hover:shadow-md flex flex-col h-full">
                <div className="mb-4">
                  <span className="inline-block px-2.5 py-1 bg-indigo-50 text-indigo-700 text-xs font-medium rounded-full mb-3">
                    {tool.category}
                  </span>
                  <h3 className="font-medium text-slate-900">{tool.name}</h3>
                </div>
                <p className="text-sm text-slate-500 leading-relaxed flex-grow">{tool.description}</p>
                <div className="mt-4 pt-4 border-t border-slate-100">
                  <button
                    onClick={() => handleExecute(tool.code)}
                    disabled={executing[tool.code] || tool.is_active === false}
                    className="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2"
                  >
                    {executing[tool.code] ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        실행 중...
                      </>
                    ) : (
                      "실행 테스트"
                    )}
                  </button>
                  {results[tool.code] && (
                    <div className={`mt-3 p-3 rounded-md text-xs ${results[tool.code].status === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
                      <p className="font-semibold">{results[tool.code].status === 'success' ? '성공' : '실패'}</p>
                      <p className="mt-1 break-all">{results[tool.code].message || JSON.stringify(results[tool.code].result)}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
