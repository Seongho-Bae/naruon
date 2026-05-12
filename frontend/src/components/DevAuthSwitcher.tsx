'use client';

import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { UserCircle } from 'lucide-react';

export function DevAuthSwitcher() {
  const [userId, setUserId] = useState('testuser');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('naruon_dev_user');
      if (stored) setUserId(stored);
    }
  }, []);

  const toggleUser = () => {
    const nextUser = userId === 'admin' ? 'testuser' : 'admin';
    localStorage.setItem('naruon_dev_user', nextUser);
    setUserId(nextUser);
    window.location.reload();
  };

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
