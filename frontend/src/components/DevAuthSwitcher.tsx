'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { getRuntimeConfig } from '@/lib/runtime-config';
import { UserCircle } from 'lucide-react';

export function DevAuthSwitcher() {
  const [userId, setUserId] = useState('testuser');
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const isLocalHost = ['localhost', '127.0.0.1'].includes(window.location.hostname);
      const hasBearer = !!apiClient.getBearerToken();
      let cancelled = false;
      getRuntimeConfig().then((config) => {
        const allowDevOverride = isLocalHost && !hasBearer && config.features.dev_header_auth_enabled;
        const timer = window.setTimeout(() => {
          if (cancelled) return;
          setVisible(allowDevOverride);
          if (!allowDevOverride) {
            return;
          }
          const stored = localStorage.getItem('naruon_dev_user');
          if (stored) {
            setUserId(stored);
          }
        }, 0);
        if (cancelled) window.clearTimeout(timer);
      }).catch(() => {
        if (!cancelled) setVisible(false);
      });
      return () => {
        cancelled = true;
      };
    }
  }, []);

  const toggleUser = () => {
    const nextUser = userId === 'admin' ? 'testuser' : 'admin';
    localStorage.setItem('naruon_dev_user', nextUser);
    setUserId(nextUser);
    window.location.reload();
  };

  if (!visible) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <Button 
        variant={userId === 'admin' ? 'default' : 'outline'}
        size="sm" 
        onClick={toggleUser}
        className="shadow-lg rounded-full"
        title="개발용 계정 스위처"
      >
        <UserCircle className="w-4 h-4 mr-2" />
        {userId === 'admin' ? '관리자 (Admin)' : '일반 (Member)'}
      </Button>
    </div>
  );
}
