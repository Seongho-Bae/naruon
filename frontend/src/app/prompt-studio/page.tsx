'use client';

import React, { useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Play, Save, Code } from 'lucide-react';

export default function PromptStudioPage() {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    content: '요약해주세요: {{email}}',
    is_shared: false
  });
  
  const [testVariable, setTestVariable] = useState('이메일 내용 예시입니다.');
  const [testResult, setTestResult] = useState('');
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTest = async () => {
    setTesting(true);
    setError(null);
    try {
      const data = await apiClient.post<any>('/api/prompts/test', {
        content: formData.content,
        variables: { email: testVariable }
      });
      setTestResult(data.result || '응답이 없습니다.');
    } catch (err: unknown) {
      setError(((err as Error).message || '') || '테스트 실패');
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await apiClient.post<any>('/api/prompts', formData);
      alert("성공적으로 저장되었습니다.");
    } catch (err: unknown) {
      setError(((err as Error).message || '') || '저장 실패');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-black text-foreground flex items-center gap-2 mb-2">
          <Code className="w-6 h-6 text-primary" />
          Prompt Studio
        </h1>
        <p className="text-muted-foreground text-sm">프롬프트를 작성, 테스트, 저장하세요.</p>
      </div>

      <div className="space-y-4">
        {error && <div className="text-red-500 text-sm bg-red-50 p-3 rounded-lg border border-red-100">{error}</div>}
        
        <Input 
          placeholder="프롬프트 이름" 
          value={formData.title} 
          onChange={e => setFormData({ ...formData, title: e.target.value })} 
        />
        <Input 
          placeholder="설명" 
          value={formData.description} 
          onChange={e => setFormData({ ...formData, description: e.target.value })} 
        />
        <Textarea 
          className="min-h-[200px] font-mono text-sm"
          value={formData.content} 
          onChange={e => setFormData({ ...formData, content: e.target.value })} 
        />
        <div className="flex items-center space-x-2">
          <Checkbox 
            id="is_shared" 
            checked={formData.is_shared} 
            onCheckedChange={(checked) => setFormData({ ...formData, is_shared: !!checked })}
          />
          <label htmlFor="is_shared" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
            워크스페이스에 공유하기
          </label>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-border pt-6">
        <div className="space-y-3">
          <h3 className="font-bold text-sm">테스트 변수 입력</h3>
          <Textarea 
            placeholder="{{email}} 변수 값" 
            value={testVariable} 
            onChange={e => setTestVariable(e.target.value)} 
          />
          <Button onClick={handleTest} disabled={testing} className="w-full">
            <Play className="w-4 h-4 mr-2" /> {testing ? '테스트 중...' : '실행 (Test)'}
          </Button>
        </div>
        <div className="space-y-3">
          <h3 className="font-bold text-sm">실행 결과</h3>
          <div className="p-4 bg-secondary/30 rounded-lg min-h-[100px] text-sm whitespace-pre-wrap border border-border">
            {testResult || '실행 결과가 여기에 표시됩니다.'}
          </div>
          <Button onClick={handleSave} disabled={saving} variant="secondary" className="w-full">
            <Save className="w-4 h-4 mr-2" /> {saving ? '저장 중...' : '프롬프트 저장 (Save)'}
          </Button>
        </div>
      </div>
    </div>
  );
}
