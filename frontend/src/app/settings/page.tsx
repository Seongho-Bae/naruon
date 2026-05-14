'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { Activity, AlertCircle, CheckCircle2, Key, Mail, Server, Settings, Shield } from 'lucide-react';

import { apiClient } from '@/lib/api-client';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

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

interface PersonalMailboxConfig {
  user_id: string;
  smtp_server: string | null;
  smtp_port: number | null;
  smtp_username: string | null;
  smtp_password: string | null;
  imap_server: string | null;
  imap_port: number | null;
  imap_username: string | null;
  imap_password: string | null;
}

interface MailboxAccount {
  id: number;
  user_id: string;
  email_address: string;
  display_name: string | null;
  provider: string;
  is_default_reply: boolean;
  is_active: boolean;
  smtp_server: string | null;
  smtp_port: number | null;
  smtp_username: string | null;
  smtp_password_set: boolean;
  imap_server: string | null;
  imap_port: number | null;
  imap_username: string | null;
  imap_password_set: boolean;
  pop3_server: string | null;
  pop3_port: number | null;
  pop3_username: string | null;
  pop3_password_set: boolean;
}

interface RunnerConfig {
  workspace_id: string;
  configured: boolean;
  fingerprint: string | null;
  updated_at: string | null;
}

function getScopedErrorMessage(err: unknown, forbiddenMessage: string, fallbackMessage: string) {
  const status = (err as Error & { status?: number }).status;
  if (status === 403) return forbiddenMessage;
  const message = (err as Error).message || '';
  return message || fallbackMessage;
}

export default function SettingsPage() {
  const currentUserId = apiClient.getCurrentUserId();
  const currentOrganizationId = apiClient.getCurrentOrganizationId();
  const canManageWorkspaceSettings = apiClient.canManageWorkspaceSettings();

  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [loadingProviders, setLoadingProviders] = useState(true);
  const [providerError, setProviderError] = useState<string | null>(null);
  const [providerForm, setProviderForm] = useState({
    name: '',
    provider_type: 'openai',
    base_url: '',
    api_key: '',
  });
  const [providerSubmitError, setProviderSubmitError] = useState<string | null>(null);
  const [providerSubmitSuccess, setProviderSubmitSuccess] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState<number | null>(null);

  const [personalForm, setPersonalForm] = useState({
    smtp_server: '',
    smtp_port: '587',
    smtp_username: '',
    smtp_password: '',
    imap_server: '',
    imap_port: '993',
    imap_username: '',
    imap_password: '',
  });
  const [personalLoading, setPersonalLoading] = useState(true);
  const [personalSubmitError, setPersonalSubmitError] = useState<string | null>(null);
  const [personalSubmitSuccess, setPersonalSubmitSuccess] = useState<string | null>(null);
  const [mailboxAccounts, setMailboxAccounts] = useState<MailboxAccount[]>([]);
  const [mailboxLoading, setMailboxLoading] = useState(true);
  const [mailboxError, setMailboxError] = useState<string | null>(null);
  const [mailboxSubmitError, setMailboxSubmitError] = useState<string | null>(null);
  const [mailboxSubmitSuccess, setMailboxSubmitSuccess] = useState<string | null>(null);
  const [editingMailboxId, setEditingMailboxId] = useState<number | null>(null);
  const [mailboxBusyId, setMailboxBusyId] = useState<number | null>(null);
  const [mailboxForm, setMailboxForm] = useState({
    email_address: '',
    display_name: '',
    provider: 'custom',
    is_default_reply: false,
    is_active: true,
    smtp_server: '',
    smtp_port: '587',
    smtp_username: '',
    smtp_password: '',
    imap_server: '',
    imap_port: '993',
    imap_username: '',
    imap_password: '',
    pop3_server: '',
    pop3_port: '995',
    pop3_username: '',
    pop3_password: '',
  });

  const [runnerConfig, setRunnerConfig] = useState<RunnerConfig | null>(null);
  const [runnerLoading, setRunnerLoading] = useState(true);
  const [runnerError, setRunnerError] = useState<string | null>(null);
  const [runnerToken, setRunnerToken] = useState<string | null>(null);
  const [runnerBusy, setRunnerBusy] = useState(false);

  const fetchProviders = useCallback(async () => {
    if (!canManageWorkspaceSettings) {
      setProviders([]);
      setProviderError(null);
      setLoadingProviders(false);
      return;
    }

    try {
      const data = await apiClient.get<LLMProvider[]>('/api/llm-providers');
      setProviders(data);
      setProviderError(null);
    } catch (err: unknown) {
      setProviderError(
        getScopedErrorMessage(
          err,
          '워크스페이스(Organization) 관리자 권한이 필요합니다. 관리자 계정으로 로그인해주세요.',
          '제공자 목록을 불러오는 데 실패했습니다.',
        ),
      );
    } finally {
      setLoadingProviders(false);
    }
  }, [canManageWorkspaceSettings]);

  const fetchPersonalConfig = useCallback(async () => {
    if (!currentUserId) {
      setPersonalLoading(false);
      return;
    }
    try {
      const data = await apiClient.get<PersonalMailboxConfig>(`/api/config?user_id=${encodeURIComponent(currentUserId)}`);
      setPersonalForm({
        smtp_server: data.smtp_server ?? '',
        smtp_port: data.smtp_port ? String(data.smtp_port) : '587',
        smtp_username: data.smtp_username ?? '',
        smtp_password: data.smtp_password === '********' ? '' : (data.smtp_password ?? ''),
        imap_server: data.imap_server ?? '',
        imap_port: data.imap_port ? String(data.imap_port) : '993',
        imap_username: data.imap_username ?? '',
        imap_password: data.imap_password === '********' ? '' : (data.imap_password ?? ''),
      });
    } catch {
      // keep defaults for first-time setup
    } finally {
      setPersonalLoading(false);
    }
  }, [currentUserId]);

  const fetchMailboxAccounts = useCallback(async () => {
    try {
      const data = await apiClient.get<{ items: MailboxAccount[] }>('/api/mailbox-accounts');
      setMailboxAccounts(data.items);
      setMailboxError(null);
    } catch (err: unknown) {
      setMailboxError((err as Error).message || '메일 계정 목록을 불러오지 못했습니다.');
    } finally {
      setMailboxLoading(false);
    }
  }, []);

  const fetchRunnerConfig = useCallback(async () => {
    if (!canManageWorkspaceSettings) {
      setRunnerConfig(null);
      setRunnerError(null);
      setRunnerLoading(false);
      return;
    }

    try {
      const data = await apiClient.get<RunnerConfig>('/api/runner-config');
      setRunnerConfig(data);
      setRunnerError(null);
    } catch (err: unknown) {
      setRunnerError(
        getScopedErrorMessage(
          err,
          '워크스페이스(Organization) 관리자 권한이 필요합니다. 관리자 계정으로 로그인해주세요.',
          'Runner 설정을 불러오는 데 실패했습니다.',
        ),
      );
    } finally {
      setRunnerLoading(false);
    }
  }, [canManageWorkspaceSettings]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void fetchProviders();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [fetchProviders]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void fetchPersonalConfig();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [fetchPersonalConfig]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void fetchMailboxAccounts();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [fetchMailboxAccounts]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void fetchRunnerConfig();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [fetchRunnerConfig]);

  const handleProviderSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProviderSubmitError(null);
    setProviderSubmitSuccess(null);

    try {
      const payload: Record<string, unknown> = {
        name: providerForm.name,
        provider_type: providerForm.provider_type,
        is_active: true,
      };
      if (providerForm.base_url) payload.base_url = providerForm.base_url;
      if (providerForm.api_key) payload.api_key = providerForm.api_key;

      if (editingId !== null) {
        await apiClient.put<LLMProvider>(`/api/llm-providers/${editingId}`, payload);
        setEditingId(null);
        setProviderSubmitSuccess('제공자가 성공적으로 수정되었습니다.');
      } else {
        await apiClient.post<LLMProvider>('/api/llm-providers', payload);
        setProviderSubmitSuccess('제공자가 성공적으로 추가되었습니다.');
      }

      setProviderForm({ name: '', provider_type: 'openai', base_url: '', api_key: '' });
      await fetchProviders();
    } catch (err: unknown) {
      setProviderSubmitError((err as Error).message || '저장에 실패했습니다.');
    }
  };

  const handlePersonalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPersonalSubmitError(null);
    setPersonalSubmitSuccess(null);

    try {
      if (!currentUserId) {
        throw new Error('개인 이메일 계정을 저장하려면 인증된 사용자 세션이 필요합니다.');
      }
      const smtpPortNum = Number(personalForm.smtp_port);
      const imapPortNum = Number(personalForm.imap_port);
      if (!Number.isInteger(smtpPortNum) || smtpPortNum < 1 || smtpPortNum > 65535) {
        throw new Error('SMTP 포트는 1~65535 범위의 정수여야 합니다.');
      }
      if (!Number.isInteger(imapPortNum) || imapPortNum < 1 || imapPortNum > 65535) {
        throw new Error('IMAP 포트는 1~65535 범위의 정수여야 합니다.');
      }

      const payload: Record<string, unknown> = {
        user_id: currentUserId,
        smtp_server: personalForm.smtp_server || null,
        smtp_port: smtpPortNum,
        smtp_username: personalForm.smtp_username || null,
        imap_server: personalForm.imap_server || null,
        imap_port: imapPortNum,
        imap_username: personalForm.imap_username || null,
      };
      if (personalForm.smtp_password.trim()) payload.smtp_password = personalForm.smtp_password;
      if (personalForm.imap_password.trim()) payload.imap_password = personalForm.imap_password;

      await apiClient.post<{ status: string }>('/api/config', {
        ...payload,
      });
      setPersonalSubmitSuccess('이메일 계정 설정이 성공적으로 저장되었습니다.');
    } catch (err: unknown) {
      setPersonalSubmitError((err as Error).message || '이메일 계정 저장에 실패했습니다.');
    }
  };

  const resetMailboxForm = () => {
    setEditingMailboxId(null);
    setMailboxForm({
      email_address: '',
      display_name: '',
      provider: 'custom',
      is_default_reply: false,
      is_active: true,
      smtp_server: '',
      smtp_port: '587',
      smtp_username: '',
      smtp_password: '',
      imap_server: '',
      imap_port: '993',
      imap_username: '',
      imap_password: '',
      pop3_server: '',
      pop3_port: '995',
      pop3_username: '',
      pop3_password: '',
    });
  };

  const handleMailboxSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMailboxSubmitError(null);
    setMailboxSubmitSuccess(null);

    try {
      const smtpPortNum = Number(mailboxForm.smtp_port);
      const imapPortNum = Number(mailboxForm.imap_port);
      const pop3PortNum = Number(mailboxForm.pop3_port);
      if (!mailboxForm.email_address.trim()) throw new Error('메일 주소는 필수입니다.');
      if (!Number.isInteger(smtpPortNum) || smtpPortNum < 1 || smtpPortNum > 65535) throw new Error('SMTP 포트는 1~65535 범위의 정수여야 합니다.');
      if (!Number.isInteger(imapPortNum) || imapPortNum < 1 || imapPortNum > 65535) throw new Error('IMAP 포트는 1~65535 범위의 정수여야 합니다.');
      if (mailboxForm.pop3_server && (!Number.isInteger(pop3PortNum) || pop3PortNum < 1 || pop3PortNum > 65535)) throw new Error('POP3 포트는 1~65535 범위의 정수여야 합니다.');

      const payload: Record<string, unknown> = {
        email_address: mailboxForm.email_address.trim(),
        display_name: mailboxForm.display_name.trim() || null,
        provider: mailboxForm.provider,
        is_default_reply: mailboxForm.is_default_reply,
        is_active: mailboxForm.is_active,
        smtp_server: mailboxForm.smtp_server || null,
        smtp_port: smtpPortNum,
        smtp_username: mailboxForm.smtp_username || null,
        imap_server: mailboxForm.imap_server || null,
        imap_port: imapPortNum,
        imap_username: mailboxForm.imap_username || null,
        pop3_server: mailboxForm.pop3_server || null,
        pop3_port: mailboxForm.pop3_server ? pop3PortNum : null,
        pop3_username: mailboxForm.pop3_username || null,
      };
      if (mailboxForm.smtp_password.trim()) payload.smtp_password = mailboxForm.smtp_password;
      if (mailboxForm.imap_password.trim()) payload.imap_password = mailboxForm.imap_password;
      if (mailboxForm.pop3_password.trim()) payload.pop3_password = mailboxForm.pop3_password;

      if (editingMailboxId !== null) {
        await apiClient.patch(`/api/mailbox-accounts/${editingMailboxId}`, payload);
        setMailboxSubmitSuccess('메일 계정이 성공적으로 수정되었습니다.');
      } else {
        await apiClient.post('/api/mailbox-accounts', payload);
        setMailboxSubmitSuccess('메일 계정이 성공적으로 추가되었습니다.');
      }
      resetMailboxForm();
      await fetchMailboxAccounts();
    } catch (err: unknown) {
      setMailboxSubmitError((err as Error).message || '메일 계정 저장에 실패했습니다.');
    }
  };

  const handleMakeDefaultReply = async (accountId: number) => {
    setMailboxBusyId(accountId);
    try {
      await apiClient.post(`/api/mailbox-accounts/${accountId}/make-default-reply`, {});
      await fetchMailboxAccounts();
    } catch (err: unknown) {
      setMailboxError((err as Error).message || '기본 회신 계정 전환에 실패했습니다.');
    } finally {
      setMailboxBusyId(null);
    }
  };

  const handleRotateRunnerToken = async () => {
    setRunnerBusy(true);
    setRunnerError(null);
    setRunnerToken(null);

    try {
      const data = await apiClient.post<{ workspace_id: string; registration_token: string }>('/api/runner-config/rotate', {});
      setRunnerToken(data.registration_token);
      await fetchRunnerConfig();
    } catch (err: unknown) {
      setRunnerError((err as Error).message || 'Runner 토큰 발급에 실패했습니다.');
    } finally {
      setRunnerBusy(false);
    }
  };

  const loading = loadingProviders || personalLoading || runnerLoading || mailboxLoading;
  if (loading) {
    return (
      <div className="p-8 text-muted-foreground flex items-center gap-2">
        <Settings className="animate-spin w-5 h-5" /> 설정을 불러오는 중...
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-black text-foreground flex items-center gap-2 mb-2">
          <Settings className="w-6 h-6 text-primary" />
          설정 (Settings)
        </h1>
        <p className="text-muted-foreground text-sm">워크스페이스 단위의 통합 관리 및 개인 계정 설정을 구성합니다.</p>
        {canManageWorkspaceSettings && currentOrganizationId ? (
          <p className="text-xs text-muted-foreground mt-2">현재 조직 스코프: {currentOrganizationId}</p>
        ) : null}
      </div>

      <Tabs defaultValue="personal" className="w-full">
        <TabsList className={`grid w-full ${canManageWorkspaceSettings ? 'grid-cols-3' : 'grid-cols-1'} mb-8`}>
          <TabsTrigger value="personal" className="font-bold"><Mail className="w-4 h-4 mr-2" /> 개인 이메일 계정</TabsTrigger>
          {canManageWorkspaceSettings ? (
            <TabsTrigger value="workspace-llm" className="font-bold"><Key className="w-4 h-4 mr-2" /> 워크스페이스 BYOK (관리자)</TabsTrigger>
          ) : null}
          {canManageWorkspaceSettings ? (
            <TabsTrigger value="workspace-runner" className="font-bold"><Activity className="w-4 h-4 mr-2" /> Self-hosted Runner (관리자)</TabsTrigger>
          ) : null}
        </TabsList>

        <TabsContent value="personal" className="space-y-6">
          <section className="bg-white rounded-2xl border border-border shadow-sm p-6 space-y-6">
            <div>
              <h2 className="font-bold text-lg mb-2">연결된 메일 계정</h2>
              <p className="text-sm text-muted-foreground">여러 개인 메일 계정을 연결하고 기본 회신 계정을 지정합니다. 추후 Gmail/iCloud/Outlook/사내 수집 경로의 기초가 됩니다.</p>
            </div>

            {mailboxError ? <div className="text-red-500 text-xs font-medium bg-red-50 p-2 rounded">{mailboxError}</div> : null}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="space-y-3">
                {mailboxAccounts.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">연결된 메일 계정이 아직 없습니다.</div>
                ) : mailboxAccounts.map((account) => (
                  <div key={account.id} className="rounded-xl border border-border bg-card/50 p-4 space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-bold text-foreground">{account.display_name || account.email_address}</p>
                        <p className="text-sm text-muted-foreground">{account.email_address}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        {account.is_default_reply ? <Badge>기본 회신 계정</Badge> : null}
                        <Badge variant={account.is_active ? 'default' : 'secondary'}>{account.is_active ? '활성' : '비활성'}</Badge>
                      </div>
                    </div>
                    <div className="grid gap-1 text-xs text-muted-foreground">
                      <p>SMTP: {account.smtp_server || '미설정'} / {account.smtp_username || '미설정'}</p>
                      <p>IMAP: {account.imap_server || '미설정'} / {account.imap_username || '미설정'}</p>
                      <p>POP3: {account.pop3_server || '미설정'} / {account.pop3_username || '미설정'}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {!account.is_default_reply ? (
                        <Button type="button" variant="outline" size="sm" onClick={() => void handleMakeDefaultReply(account.id)} disabled={mailboxBusyId === account.id}>
                          {mailboxBusyId === account.id ? '전환 중...' : '기본 회신으로 지정'}
                        </Button>
                      ) : null}
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setEditingMailboxId(account.id);
                          setMailboxForm({
                            email_address: account.email_address,
                            display_name: account.display_name || '',
                            provider: account.provider,
                            is_default_reply: account.is_default_reply,
                            is_active: account.is_active,
                            smtp_server: account.smtp_server || '',
                            smtp_port: account.smtp_port ? String(account.smtp_port) : '587',
                            smtp_username: account.smtp_username || '',
                            smtp_password: '',
                            imap_server: account.imap_server || '',
                            imap_port: account.imap_port ? String(account.imap_port) : '993',
                            imap_username: account.imap_username || '',
                            imap_password: '',
                            pop3_server: account.pop3_server || '',
                            pop3_port: account.pop3_port ? String(account.pop3_port) : '995',
                            pop3_username: account.pop3_username || '',
                            pop3_password: '',
                          });
                        }}
                      >
                        수정
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              <form onSubmit={handleMailboxSubmit} className="rounded-xl border border-border bg-secondary/20 p-4 space-y-4 h-fit">
                <div>
                  <h3 className="font-bold">{editingMailboxId !== null ? '메일 계정 수정' : '메일 계정 추가'}</h3>
                  <p className="text-xs text-muted-foreground mt-1">개별 계정별 회신/수신 자격 증명을 저장합니다.</p>
                </div>
                <Input placeholder="account@example.com" value={mailboxForm.email_address} onChange={(e) => setMailboxForm({ ...mailboxForm, email_address: e.target.value })} />
                <Input placeholder="표시 이름 (예: Personal Gmail)" value={mailboxForm.display_name} onChange={(e) => setMailboxForm({ ...mailboxForm, display_name: e.target.value })} />
                <Input placeholder="provider (예: custom / gmail / outlook / icloud)" value={mailboxForm.provider} onChange={(e) => setMailboxForm({ ...mailboxForm, provider: e.target.value })} />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <Input placeholder="smtp.example.com" value={mailboxForm.smtp_server} onChange={(e) => setMailboxForm({ ...mailboxForm, smtp_server: e.target.value })} />
                  <Input placeholder="587" value={mailboxForm.smtp_port} onChange={(e) => setMailboxForm({ ...mailboxForm, smtp_port: e.target.value })} />
                  <Input placeholder="smtp 사용자명" value={mailboxForm.smtp_username} onChange={(e) => setMailboxForm({ ...mailboxForm, smtp_username: e.target.value })} />
                  <Input type="password" placeholder="smtp 비밀번호" value={mailboxForm.smtp_password} onChange={(e) => setMailboxForm({ ...mailboxForm, smtp_password: e.target.value })} />
                  <Input placeholder="imap.example.com" value={mailboxForm.imap_server} onChange={(e) => setMailboxForm({ ...mailboxForm, imap_server: e.target.value })} />
                  <Input placeholder="993" value={mailboxForm.imap_port} onChange={(e) => setMailboxForm({ ...mailboxForm, imap_port: e.target.value })} />
                  <Input placeholder="imap 사용자명" value={mailboxForm.imap_username} onChange={(e) => setMailboxForm({ ...mailboxForm, imap_username: e.target.value })} />
                  <Input type="password" placeholder="imap 비밀번호" value={mailboxForm.imap_password} onChange={(e) => setMailboxForm({ ...mailboxForm, imap_password: e.target.value })} />
                  <Input placeholder="pop.example.com (선택)" value={mailboxForm.pop3_server} onChange={(e) => setMailboxForm({ ...mailboxForm, pop3_server: e.target.value })} />
                  <Input placeholder="995" value={mailboxForm.pop3_port} onChange={(e) => setMailboxForm({ ...mailboxForm, pop3_port: e.target.value })} />
                  <Input placeholder="pop3 사용자명" value={mailboxForm.pop3_username} onChange={(e) => setMailboxForm({ ...mailboxForm, pop3_username: e.target.value })} />
                  <Input type="password" placeholder="pop3 비밀번호" value={mailboxForm.pop3_password} onChange={(e) => setMailboxForm({ ...mailboxForm, pop3_password: e.target.value })} />
                </div>
                <label className="flex items-center gap-2 text-sm text-foreground">
                  <input type="checkbox" checked={mailboxForm.is_default_reply} onChange={(e) => setMailboxForm({ ...mailboxForm, is_default_reply: e.target.checked })} />
                  기본 회신 계정으로 지정
                </label>
                <label className="flex items-center gap-2 text-sm text-foreground">
                  <input type="checkbox" checked={mailboxForm.is_active} onChange={(e) => setMailboxForm({ ...mailboxForm, is_active: e.target.checked })} />
                  활성 상태 유지
                </label>
                {mailboxSubmitError ? <div className="text-red-500 text-xs font-medium bg-red-50 p-2 rounded">{mailboxSubmitError}</div> : null}
                {mailboxSubmitSuccess ? <div className="text-green-600 text-xs font-medium bg-green-50 p-2 rounded">{mailboxSubmitSuccess}</div> : null}
                <div className="flex gap-2 justify-end">
                  {editingMailboxId !== null ? <Button type="button" variant="outline" onClick={resetMailboxForm}>취소</Button> : null}
                  <Button type="submit">{editingMailboxId !== null ? '메일 계정 저장' : '메일 계정 추가'}</Button>
                </div>
              </form>
            </div>
          </section>

          <section className="bg-white rounded-2xl border border-border shadow-sm p-6">
            <h2 className="font-bold text-lg mb-2">레거시 단일 계정 설정</h2>
            <p className="text-sm text-muted-foreground mb-6">기존 단일 계정 경로와의 호환성을 위해 남겨둔 설정입니다. 신규 연결은 위의 메일 계정 목록을 우선 사용합니다.</p>
            <form onSubmit={handlePersonalSubmit} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="font-bold text-sm">SMTP 발송 설정</h3>
                <Input placeholder="smtp.example.com" value={personalForm.smtp_server} onChange={(e) => setPersonalForm({ ...personalForm, smtp_server: e.target.value })} />
                <Input placeholder="587" value={personalForm.smtp_port} onChange={(e) => setPersonalForm({ ...personalForm, smtp_port: e.target.value })} />
                <Input placeholder="smtp 사용자명" value={personalForm.smtp_username} onChange={(e) => setPersonalForm({ ...personalForm, smtp_username: e.target.value })} />
                <Input type="password" placeholder="smtp 비밀번호 또는 앱 비밀번호" value={personalForm.smtp_password} onChange={(e) => setPersonalForm({ ...personalForm, smtp_password: e.target.value })} />
              </div>
              <div className="space-y-4">
                <h3 className="font-bold text-sm">IMAP 수신 설정</h3>
                <Input placeholder="imap.example.com" value={personalForm.imap_server} onChange={(e) => setPersonalForm({ ...personalForm, imap_server: e.target.value })} />
                <Input placeholder="993" value={personalForm.imap_port} onChange={(e) => setPersonalForm({ ...personalForm, imap_port: e.target.value })} />
                <Input placeholder="imap 사용자명" value={personalForm.imap_username} onChange={(e) => setPersonalForm({ ...personalForm, imap_username: e.target.value })} />
                <Input type="password" placeholder="imap 비밀번호 또는 앱 비밀번호" value={personalForm.imap_password} onChange={(e) => setPersonalForm({ ...personalForm, imap_password: e.target.value })} />
              </div>
              <div className="lg:col-span-2 space-y-3">
                {personalSubmitError && <div className="text-red-500 text-xs font-medium bg-red-50 p-2 rounded">{personalSubmitError}</div>}
                {personalSubmitSuccess && <div className="text-green-600 text-xs font-medium bg-green-50 p-2 rounded">{personalSubmitSuccess}</div>}
                <div className="flex justify-end">
                  <Button type="submit">계정 저장</Button>
                </div>
              </div>
            </form>
          </section>
        </TabsContent>

        {canManageWorkspaceSettings ? (
          <TabsContent value="workspace-llm" className="space-y-6">
            {providerError ? (
              <div className="bg-red-50 text-red-600 p-4 rounded-xl border border-red-100 flex items-start gap-3">
                <Shield className="w-5 h-5 shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-bold">접근 거부</h3>
                  <p className="text-sm mt-1">{providerError}</p>
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
                    providers.map((p) => (
                      <div key={p.id} className="p-4 rounded-xl border border-border bg-card/50 flex flex-col gap-2">
                        <div className="flex items-center justify-between">
                          <span className="font-bold">{p.name}</span>
                          <div className="flex items-center gap-2">
                            <Badge variant={p.is_active ? 'default' : 'secondary'}>{p.is_active ? '활성' : '비활성'}</Badge>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 text-[11px] px-2"
                              onClick={() => {
                                setEditingId(p.id);
                                setProviderForm({
                                  name: p.name,
                                  provider_type: p.provider_type,
                                  base_url: p.base_url || '',
                                  api_key: '',
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
                                if (!confirm('정말 이 제공자를 삭제하시겠습니까?')) return;
                                setIsDeleting(p.id);
                                try {
                                  await apiClient.delete(`/api/llm-providers/${p.id}`);
                                  await fetchProviders();
                                  if (editingId === p.id) {
                                    setEditingId(null);
                                    setProviderForm({ name: '', provider_type: 'openai', base_url: '', api_key: '' });
                                  }
                                } catch (e: unknown) {
                                  alert('삭제 실패: ' + ((e as Error).message || ''));
                                } finally {
                                  setIsDeleting(null);
                                }
                              }}
                            >
                              {isDeleting === p.id ? '삭제중...' : '삭제'}
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
                <h3 className="font-bold mb-4">{editingId !== null ? '제공자 수정' : '새 제공자 추가 (BYOK)'}</h3>
                <form onSubmit={handleProviderSubmit} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground">식별 이름</label>
                    <Input required placeholder="예: 사내 보안용 Ollama" value={providerForm.name} onChange={(e) => setProviderForm({ ...providerForm, name: e.target.value })} />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground">제공자 유형</label>
                    <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" value={providerForm.provider_type} onChange={(e) => setProviderForm({ ...providerForm, provider_type: e.target.value })}>
                      <option value="openai">OpenAI 호환</option>
                      <option value="anthropic">Anthropic</option>
                      <option value="gemini">Google Gemini</option>
                      <option value="ollama">Local Ollama</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground">Base URL (선택)</label>
                    <Input placeholder="https://api.openai.com/v1" value={providerForm.base_url} onChange={(e) => setProviderForm({ ...providerForm, base_url: e.target.value })} />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground">API Key (시크릿)</label>
                    <Input type="password" placeholder={editingId !== null ? '변경하려면 새 키를 입력하세요' : '새로운 키를 입력하세요'} value={providerForm.api_key} onChange={(e) => setProviderForm({ ...providerForm, api_key: e.target.value })} />
                  </div>
                  {providerSubmitError && <div className="text-red-500 text-xs font-medium bg-red-50 p-2 rounded">{providerSubmitError}</div>}
                  {providerSubmitSuccess && <div className="text-green-600 text-xs font-medium bg-green-50 p-2 rounded">{providerSubmitSuccess}</div>}
                  <div className="flex gap-2 pt-2">
                    <Button type="submit" className="flex-1 font-bold">{editingId !== null ? '수정 반영' : '저장 및 활성화'}</Button>
                    {editingId !== null && (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => {
                          setEditingId(null);
                          setProviderForm({ name: '', provider_type: 'openai', base_url: '', api_key: '' });
                          setProviderSubmitError(null);
                          setProviderSubmitSuccess(null);
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
        ) : null}

        {canManageWorkspaceSettings ? (
          <TabsContent value="workspace-runner" className="space-y-6">
            {runnerError ? (
              <div className="bg-red-50 text-red-600 p-4 rounded-xl border border-red-100 flex items-start gap-3">
                <Shield className="w-5 h-5 shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-bold">접근 거부</h3>
                  <p className="text-sm mt-1">{runnerError}</p>
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

              <div className="mb-4 rounded-xl border border-border bg-secondary/20 p-4 text-sm">
                <p className="font-semibold">현재 Runner 구성</p>
                <p className="text-muted-foreground mt-1">조직 스코프: {runnerConfig?.workspace_id || 'default-workspace'}</p>
                <p className="text-muted-foreground">토큰 상태: {runnerConfig?.configured ? `Configured (${runnerConfig.fingerprint})` : '미발급'}</p>
              </div>

              <div className="bg-slate-900 rounded-xl p-4 font-mono text-sm text-slate-300 mb-6">
                <p className="text-slate-500 mb-2"># 사내망 서버에서 아래 명령어로 Runner를 실행하세요.</p>
                <p><span className="text-green-400">docker run</span> -d --name naruon-runner \\</p>
                <p>  -e <span className="text-blue-300">RUNNER_TOKEN</span>=<span className="text-yellow-300">&quot;{runnerToken || '발급받은_조직_토큰'}&quot;</span> \\</p>
                <p>  ghcr.io/seongho-bae/naruon-runner:latest</p>
              </div>

              {runnerToken && <div className="text-green-600 text-xs font-medium bg-green-50 p-2 rounded mb-3">새 Runner 토큰이 발급되었습니다. 지금 복사해 두세요.</div>}

              <div className="flex justify-end">
                <Button disabled={runnerBusy} onClick={handleRotateRunnerToken}>{runnerBusy ? '발급 중...' : '새 Runner 토큰 발급'}</Button>
              </div>
              </section>
            )}
          </TabsContent>
        ) : null}
      </Tabs>
    </div>
  );
}
