'use client';

import React, { useEffect, useState } from 'react';
import { KeyRound, ShieldCheck, LogOut } from 'lucide-react';

import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { getRuntimeConfig, type RuntimeConfig } from '@/lib/runtime-config';

function decodeClaims() {
  return apiClient.getSessionClaims();
}

export default function LoginPage() {
  const [token, setToken] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [runtimeConfig, setRuntimeConfig] = useState<RuntimeConfig | null>(null);
  const claims = decodeClaims();
  const canUseManualBearerSession = apiClient.canUseManualBearerSession() && !!runtimeConfig?.features.manual_bearer_login_enabled;

  useEffect(() => {
    let active = true;
    getRuntimeConfig().then((config) => {
      if (active) setRuntimeConfig(config);
    }).catch(() => {
      if (active) setRuntimeConfig(null);
    });
    return () => {
      active = false;
    };
  }, []);

  const saveToken = () => {
    if (!canUseManualBearerSession) {
      setMessage('수동 Bearer 토큰 저장은 로컬 검증 환경에서만 허용됩니다.');
      return;
    }
    if (!token.trim()) {
      setMessage('Bearer 토큰을 입력하세요.');
      return;
    }
    apiClient.setBearerToken(token);
    setToken('');
    setMessage('OIDC bearer 토큰이 저장되었습니다.');
    window.location.reload();
  };

  const clearToken = () => {
    apiClient.clearBearerToken();
    setMessage('OIDC bearer 토큰이 제거되었습니다.');
    window.location.reload();
  };

  return (
    <div className="mx-auto max-w-2xl p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-black flex items-center gap-2"><ShieldCheck className="w-6 h-6 text-primary" /> 로그인 / 세션</h1>
        <p className="text-sm text-muted-foreground mt-2">
          실제 배포에서는 Keycloak/Casdoor OIDC 로그인으로 전환됩니다. 현재 수동 Bearer 토큰 입력은 로컬 검증 환경에서만 허용되며, 원격 환경에서는 IdP 기반 세션 플로우로 대체될 예정입니다.
        </p>
      </div>

      {canUseManualBearerSession ? (
        <div className="rounded-2xl border border-border bg-card p-5 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-semibold">OIDC Bearer 토큰</label>
            <Input value={token} onChange={(e) => setToken(e.target.value)} placeholder="eyJhbGciOi..." />
          </div>
          <div className="flex gap-3">
            <Button onClick={saveToken}><KeyRound className="w-4 h-4 mr-2" />토큰 저장</Button>
            <Button variant="outline" onClick={clearToken}><LogOut className="w-4 h-4 mr-2" />토큰 제거</Button>
          </div>
          {message && <div className="text-sm text-primary">{message}</div>}
        </div>
      ) : (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
          수동 Bearer 토큰 입력은 이 스택에서 활성화되어 있지 않습니다. OIDC provider/session 구성이 필요합니다.
        </div>
      )}

      <div className="rounded-2xl border border-border bg-secondary/20 p-5 space-y-2">
        <h2 className="font-bold">현재 세션 claims</h2>
        {claims ? (
          <pre className="text-xs overflow-auto whitespace-pre-wrap">{JSON.stringify(claims, null, 2)}</pre>
        ) : (
          <p className="text-sm text-muted-foreground">저장된 Bearer 토큰이 없습니다. 로컬 검증은 서명된 Bearer 토큰이나 OIDC provider/session 구성이 필요합니다.</p>
        )}
      </div>
    </div>
  );
}
