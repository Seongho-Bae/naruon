'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Settings, Shield, Server, CheckCircle2, AlertCircle, Mail, Activity, Key } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

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

  useEffect(() => {
    const fetchProvidersData = async () => {
      try {
        const data = await apiClient.get<LLMProvider[]>('/api/llm-providers');
        setProviders(data);
        setError(null);
      } catch (err: unknown) {
        if (((err as Error).message || '').includes('403')) {
          setError('워크스페이스(Organization) 관리자 권한이 필요합니다. 관리자 계정으로 로그인해주세요.');
        } else {
          setError('데이터를 불러오는 데 실패했습니다.');
        }
      } finally {
        setLoading(false);
      }
    };
    void fetchProvidersData();
  }, []);

  const fetchProviders = async () => {
    try {
      const data = await apiClient.get<LLMProvider[]>('/api/llm-providers');
      setProviders(data);
      setError(null);
    } catch (err: unknown) {
      if (((err as Error).message || '').includes('403')) {
        setError('워크스페이스(Organization) 관리자 권한이 필요합니다. 관리자 계정으로 로그인해주세요.');
      } else {
        setError('데이터를 불러오는 데 실패했습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-black text-foreground flex items-center gap-2 mb-2">
          <Settings className="w-6 h-6 text-primary" />
          설정 (Settings)
        </h1>
        <p className="text-muted-foreground text-sm">
          워크스페이스 단위의 통합 관리 및 개인 계정 설정을 구성합니다.
        </p>
      </div>

      <Tabs defaultValue="personal" className="w-full">
        <TabsList className="grid w-full grid-cols-3 mb-8">
          <TabsTrigger value="personal" className="font-bold"><Mail className="w-4 h-4 mr-2"/> 개인 이메일 계정</TabsTrigger>
          <TabsTrigger value="workspace-llm" className="font-bold"><Key className="w-4 h-4 mr-2"/> 워크스페이스 BYOK (관리자)</TabsTrigger>
          <TabsTrigger value="workspace-runner" className="font-bold"><Activity className="w-4 h-4 mr-2"/> Self-hosted Runner (관리자)</TabsTrigger>
        </TabsList>

        <TabsContent value="personal" className="space-y-6">
          <section className="bg-white rounded-2xl border border-border shadow-sm p-6">
            <h2 className="font-bold text-lg mb-2">개인 이메일 계정 연결</h2>
            <p className="text-sm text-muted-foreground mb-6">
              Naruon 워크스페이스에서 사용할 본인의 IMAP/SMTP 이메일 계정을 연결합니다. (개인 단위 설정)
            </p>
            <div className="bg-secondary/30 border border-border rounded-xl p-8 flex flex-col items-center justify-center text-center">
              <Mail className="w-10 h-10 text-muted-foreground mb-3 opacity-50" />
              <h3 className="font-bold text-foreground mb-1">등록된 이메일 계정이 없습니다.</h3>
              <p className="text-sm text-muted-foreground mb-4">현재 IMAP/SMTP 연동 기능 UI는 준비 중입니다. 백엔드는 구현 완료되었습니다.</p>
              <Button disabled variant="outline">계정 추가하기 (준비 중)</Button>
            </div>
          </section>
        </TabsContent>

        <TabsContent value="workspace-llm" className="space-y-6">
          {error ? (
            <div className="bg-red-50 text-red-600 p-4 rounded-xl border border-red-100 flex items-start gap-3">
              <Shield className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <h3 className="font-bold">접근 거부</h3>
                <p className="text-sm mt-1">{error}</p>
                <p className="text-xs mt-2 opacity-80">※ 현재 Naruon 시스템 관리자가 아닌 조직(Organization) 단위의 관리자 권한이 필요합니다.</p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <section className="bg-white rounded-2xl border border-border shadow-sm overflow-hidden flex flex-col">
                <div className="border-b border-border bg-secondary/30 p-4">
                  <h2 className="font-bold text-foreground flex items-center gap-2">
                    <Server className="w-4 h-4" /> 등록된 조직 LLM 제공자
                  </h2>
                  <p className="text-xs text-muted-foreground mt-1">워크스페이스 멤버 전체가 공유하는 BYOK(Bring Your Own Key) 모델입니다.</p>
                </div>
                <div className="p-4 space-y-4 flex-1 overflow-auto">
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

              <section className="bg-white rounded-2xl border border-border shadow-sm p-5 h-fit">
                <h3 className="font-bold mb-4">{editingId ? "제공자 수정" : "새 제공자 추가 (BYOK)"}</h3>
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
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
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
                      placeholder={editingId ? "변경하려면 새 키를 입력하세요" : "새로운 키를 입력하세요"} 
                      value={formData.api_key} 
                      onChange={e => setFormData({ ...formData, api_key: e.target.value })}
                    />
                  </div>

                  {submitError && <div className="text-red-500 text-xs font-medium bg-red-50 p-2 rounded">{submitError}</div>}
                  {submitSuccess && <div className="text-green-600 text-xs font-medium bg-green-50 p-2 rounded">제공자가 성공적으로 저장되었습니다.</div>}

                  <div className="flex gap-2 pt-2">
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
          )}
        </TabsContent>

        <TabsContent value="workspace-runner" className="space-y-6">
          {error ? (
            <div className="bg-red-50 text-red-600 p-4 rounded-xl border border-red-100 flex items-start gap-3">
              <Shield className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <h3 className="font-bold">접근 거부</h3>
                <p className="text-sm mt-1">{error}</p>
              </div>
            </div>
          ) : (
            <section className="bg-white rounded-2xl border border-border shadow-sm p-6">
              <div className="flex items-start gap-4 mb-6">
                <div className="bg-primary/10 p-3 rounded-xl text-primary">
                  <Activity className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="font-bold text-lg">조직 내 Self-hosted Runner 연결</h2>
                  <p className="text-sm text-muted-foreground mt-1 leading-relaxed">
                    Naruon은 클라우드에서 사내망의 폐쇄적인 IMAP/SMTP 서버로 직접 접속하지 않습니다. <br />
                    조직(Organization) 단위의 Runner(Relay Proxy) 토큰을 발급받아 사내망에 설치하시면 안전하게 메일 트래픽이 중계됩니다.
                  </p>
                </div>
              </div>
              <div className="bg-slate-900 rounded-xl p-4 font-mono text-sm text-slate-300 mb-6">
                <p className="text-slate-500 mb-2"># 사내망 서버에서 아래 명령어로 Runner를 실행하세요.</p>
                <p><span className="text-green-400">docker run</span> -d --name naruon-runner \\</p>
                <p>  -e <span className="text-blue-300">RUNNER_TOKEN</span>=<span className="text-yellow-300">&quot;발급받은_조직_토큰&quot;</span> \\</p>
                <p>  ghcr.io/seongho-bae/naruon-runner:latest</p>
              </div>

              <div className="flex justify-end">
                <Button disabled>새 Runner 토큰 발급 (준비 중)</Button>
              </div>
            </section>
          )}
        </TabsContent>
      </Tabs>


    </div>
  );
}
