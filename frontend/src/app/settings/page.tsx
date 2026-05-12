'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Settings, Shield, Server, CheckCircle2, AlertCircle } from 'lucide-react';

interface LLMProvider {
  id: number;
  name: string;
  provider_type: string;
  base_url: string | null;
  is_active: boolean;
  configured: boolean;
  fingerprint: string | null;
  updated_at: string;
}

export default function SettingsPage() {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    provider_type: 'openai',
    base_url: '',
    api_key: ''
  });
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState<number | null>(null);

  const fetchProviders = async () => {
    try {
      // setLoading(true);
      const data = await apiClient.get<LLMProvider[]>('/api/llm-providers');
      setProviders(data);
      setError(null);
    } catch (err: unknown) {
      if (((err as Error).message || '')?.includes('403')) {
        setError('관리자 권한이 필요합니다. 관리자 계정으로 로그인해주세요.');
      } else {
        setError('제공자 목록을 불러오는 데 실패했습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const runFetch = async () => {
      try {
        const data = await apiClient.get<LLMProvider[]>('/api/llm-providers');
        setProviders(data);
        setError(null);
      } catch (err: unknown) {
        if (((err as Error).message || '').includes('403')) {
          setError('관리자 권한이 필요합니다. 관리자 계정으로 로그인해주세요.');
        } else {
          setError('제공자 목록을 불러오는 데 실패했습니다.');
        }
      } finally {
        setLoading(false);
      }
    };
    runFetch();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    setSubmitSuccess(false);

    try {
      const payload: Record<string, unknown> = {
        name: formData.name,
        provider_type: formData.provider_type,
        is_active: true
      };
      if (formData.base_url) payload.base_url = formData.base_url;
      if (formData.api_key) payload.api_key = formData.api_key;

      if (editingId) {
        await apiClient.put<LLMProvider>(`/api/llm-providers/${editingId}`, payload);
        setEditingId(null);
      } else {
        await apiClient.post<LLMProvider>('/api/llm-providers', payload);
      }
      setSubmitSuccess(true);
      setFormData({ name: '', provider_type: 'openai', base_url: '', api_key: '' });
      fetchProviders();
    } catch (err: unknown) {
      setSubmitError(((err as Error).message || '') || '저장에 실패했습니다.');
    }
  };

  if (loading) {
    return <div className="p-8 text-muted-foreground flex items-center gap-2"><Settings className="animate-spin w-5 h-5"/> 설정을 불러오는 중...</div>;
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 text-red-600 p-4 rounded-xl border border-red-100 flex items-start gap-3">
          <Shield className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <h3 className="font-bold">접근 거부</h3>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-black text-foreground flex items-center gap-2 mb-2">
          <Settings className="w-6 h-6 text-primary" />
          Naruon 설정
        </h1>
        <p className="text-muted-foreground text-sm">LLM 모델 라우팅, 보안 및 워크스페이스 설정을 관리합니다.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-6">
          <section className="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
            <div className="border-b border-border bg-secondary/30 p-4">
              <h2 className="font-bold text-foreground flex items-center gap-2">
                <Server className="w-4 h-4" /> 등록된 AI 모델 제공자
              </h2>
            </div>
            <div className="p-4 space-y-4">
              {providers.length === 0 ? (
                <div className="text-sm text-muted-foreground text-center py-8">등록된 제공자가 없습니다.</div>
              ) : (
                providers.map(p => (
                  <div key={p.id} className="p-4 rounded-xl border border-border bg-card/50 flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold">{p.name}</span>
                      <div className="flex items-center gap-2">
                        <Badge variant={p.is_active ? "default" : "secondary"}>
                          {p.is_active ? "활성" : "비활성"}
                        </Badge>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="h-6 text-[11px] px-2"
                          onClick={() => {
                            setEditingId(p.id);
                            setFormData({
                              name: p.name,
                              provider_type: p.provider_type,
                              base_url: p.base_url || '',
                              api_key: ''
                            });
                          }}
                        >
                          수정
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="h-6 text-[11px] px-2 text-red-500 hover:text-red-600 hover:bg-red-50"
                          disabled={isDeleting === p.id}
                          onClick={async () => {
                            if (!confirm("정말 이 제공자를 삭제하시겠습니까?")) return;
                            setIsDeleting(p.id);
                            try {
                              await apiClient.delete(`/api/llm-providers/${p.id}`);
                              fetchProviders();
                              if (editingId === p.id) {
                                setEditingId(null);
                                setFormData({ name: '', provider_type: 'openai', base_url: '', api_key: '' });
                              }
                            } catch (e: unknown) {
                              alert("삭제 실패: " + ((e as Error).message || ""));
                            } finally {
                              setIsDeleting(null);
                            }
                          }}
                        >
                          {isDeleting === p.id ? "삭제중..." : "삭제"}
                        </Button>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground font-mono bg-secondary/50 p-2 rounded-lg">
                      <p>Type: {p.provider_type}</p>
                      {p.base_url && <p>Base URL: {p.base_url}</p>}
                      <p className="flex items-center gap-1 mt-1">
                        Secret: 
                        {p.configured ? (
                          <span className="text-green-600 font-bold bg-green-50 px-1.5 py-0.5 rounded flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Configured ({p.fingerprint})
                          </span>
                        ) : (
                          <span className="text-red-500 font-bold bg-red-50 px-1.5 py-0.5 rounded flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" /> Missing
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </section>
        </div>

        <div>
          <section className="bg-white rounded-2xl border border-border shadow-sm p-5 sticky top-8">
            <h3 className="font-bold mb-4">{editingId ? "제공자 수정" : "새 제공자 추가"}</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">식별 이름</label>
                <Input 
                  required
                  placeholder="예: 사내 보안용 Ollama" 
                  value={formData.name} 
                  onChange={e => setFormData({ ...formData, name: e.target.value })}
                />
              </div>
              
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">제공자 유형</label>
                <select 
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={formData.provider_type}
                  onChange={e => setFormData({ ...formData, provider_type: e.target.value })}
                >
                  <option value="openai">OpenAI 호환</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="ollama">Local Ollama</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">Base URL (선택)</label>
                <Input 
                  placeholder="https://api.openai.com/v1" 
                  value={formData.base_url} 
                  onChange={e => setFormData({ ...formData, base_url: e.target.value })}
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">API Key (시크릿)</label>
                <Input 
                  type="password"
                  placeholder="새로운 키를 입력하세요" 
                  value={formData.api_key} 
                  onChange={e => setFormData({ ...formData, api_key: e.target.value })}
                />
              </div>

              {submitError && <div className="text-red-500 text-xs font-medium bg-red-50 p-2 rounded">{submitError}</div>}
              {submitSuccess && <div className="text-green-600 text-xs font-medium bg-green-50 p-2 rounded">제공자가 성공적으로 저장되었습니다.</div>}

              <div className="flex gap-2">
                <Button type="submit" className="flex-1 font-bold">
                  {editingId ? "수정 반영" : "저장 및 활성화"}
                </Button>
                {editingId && (
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => {
                      setEditingId(null);
                      setFormData({ name: '', provider_type: 'openai', base_url: '', api_key: '' });
                      setSubmitError(null);
                      setSubmitSuccess(false);
                    }}
                  >
                    취소
                  </Button>
                )}
              </div>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
