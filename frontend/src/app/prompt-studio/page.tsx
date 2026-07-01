'use client';

import React, { useMemo, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  AlertCircle,
  CheckCircle2,
  Code,
  FileText,
  Loader2,
  Play,
  Save,
  Share2,
  Sparkles,
  Variable,
} from 'lucide-react';

type PromptFormData = {
  title: string;
  description: string;
  content: string;
  is_shared: boolean;
};

type VariableValues = Record<string, string>;

const DEFAULT_CONTENT = '핵심 맥락을 종합해주세요: {{email}}';
const PLACEHOLDER_PATTERN = /\{\{([A-Za-z_][A-Za-z0-9_]{0,63})\}\}/g;

function createVariableValueMap(entries: Iterable<readonly [string, string]> = []): VariableValues {
  const values = Object.create(null) as VariableValues;
  for (const [key, value] of entries) {
    values[key] = value;
  }
  return values;
}

const DEFAULT_VARIABLE_VALUES = createVariableValueMap([
  ['email', '메일 내용 예시입니다.'],
]);

function getOwnVariableValue(values: VariableValues, key: string) {
  return Object.prototype.hasOwnProperty.call(values, key) ? values[key] : undefined;
}

function extractPromptVariables(content: string) {
  const variables = new Set<string>();
  for (const match of content.matchAll(PLACEHOLDER_PATTERN)) {
    variables.add(match[1]);
  }
  return Array.from(variables);
}

function renderPromptPreview(content: string, variables: VariableValues) {
  return content.replace(PLACEHOLDER_PATTERN, (placeholder, name: string) => {
    const value = getOwnVariableValue(variables, name);
    return value?.trim() ? value : placeholder;
  });
}

function syncVariableValues(variableNames: string[], currentValues: VariableValues) {
  const nextValues = createVariableValueMap();
  for (const variableName of variableNames) {
    nextValues[variableName] =
      getOwnVariableValue(currentValues, variableName) ??
      getOwnVariableValue(DEFAULT_VARIABLE_VALUES, variableName) ??
      '';
  }
  return nextValues;
}

function getSafeErrorSummary(error: unknown, fallback: string) {
  return error instanceof Error && error.message ? error.message : fallback;
}

export default function PromptStudioPage() {
  const [formData, setFormData] = useState<PromptFormData>({
    title: '',
    description: '',
    content: DEFAULT_CONTENT,
    is_shared: false,
  });
  const promptVariables = useMemo(() => extractPromptVariables(formData.content), [formData.content]);
  const [variableValues, setVariableValues] = useState<VariableValues>(() =>
    createVariableValueMap(Object.entries(DEFAULT_VARIABLE_VALUES)),
  );
  const [testResult, setTestResult] = useState('');
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const previewText = useMemo(
    () => renderPromptPreview(formData.content, variableValues),
    [formData.content, variableValues],
  );

  const setFormField = <Key extends keyof PromptFormData>(field: Key, value: PromptFormData[Key]) => {
    setError(null);
    setSaveStatus(null);
    setFormData((current) => ({ ...current, [field]: value }));
  };

  const setPromptContent = (content: string) => {
    setError(null);
    setSaveStatus(null);
    setFormData((current) => ({ ...current, content }));
    setVariableValues((currentValues) => syncVariableValues(extractPromptVariables(content), currentValues));
  };

  const buildVariablesPayload = () => {
    const payload = createVariableValueMap();
    for (const variableName of promptVariables) {
      payload[variableName] = getOwnVariableValue(variableValues, variableName) ?? '';
    }
    return payload;
  };

  const validateForSave = () => {
    if (!formData.title.trim()) {
      setError('프롬프트 이름을 입력하세요.');
      return false;
    }
    if (!formData.content.trim()) {
      setError('프롬프트 내용을 입력하세요.');
      return false;
    }
    return true;
  };

  const handleTest = async () => {
    setTesting(true);
    setError(null);
    setSaveStatus(null);
    try {
      const data = await apiClient.post<{ result?: string }>('/api/prompts/test', {
        content: formData.content,
        variables: buildVariablesPayload(),
      });
      setTestResult(data.result || '응답이 없습니다.');
    } catch (err: unknown) {
      setError(getSafeErrorSummary(err, '테스트 실패'));
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!validateForSave()) return;
    setSaving(true);
    setError(null);
    setSaveStatus(null);
    try {
      await apiClient.post<{ result?: string }>('/api/prompts', {
        title: formData.title.trim(),
        description: formData.description.trim() || null,
        content: formData.content,
        is_shared: formData.is_shared,
      });
      setSaveStatus('프롬프트가 저장되었습니다. AI 허브에서 실행 후보와 평가 근거로 연결됩니다.');
    } catch (err: unknown) {
      setError(getSafeErrorSummary(err, '저장 실패'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="h-full min-h-0 overflow-y-auto bg-background text-foreground">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 p-4 pb-[calc(6rem+env(safe-area-inset-bottom))] md:p-8">
        <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_22rem]">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="gap-1 border-primary/20 bg-primary/10 font-black text-primary">
                <Sparkles className="size-3" aria-hidden="true" />
                AI Hub source
              </Badge>
              <Badge variant={formData.is_shared ? 'default' : 'secondary'} className="font-black">
                {formData.is_shared ? '워크스페이스 공유' : '개인 초안'}
              </Badge>
            </div>
            <h1 className="mt-3 flex items-center gap-3 text-2xl font-black md:text-3xl">
              <Code className="size-7 text-primary" aria-hidden="true" />
              Prompt Studio
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
              원본 변수, 실행 미리보기, 저장 범위를 한 화면에서 확인한 뒤 AI 허브 실행 후보로 넘깁니다.
            </p>
          </div>

          <Card size="sm" className="bg-card/90">
            <CardHeader>
              <CardTitle className="text-sm font-black">개발 계약 상태</CardTitle>
              <CardDescription>Figma와 코드가 함께 보장해야 하는 필수 상태</CardDescription>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-3 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <dt className="font-bold text-muted-foreground">변수</dt>
                  <dd className="font-black text-primary">{promptVariables.length}개</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="font-bold text-muted-foreground">저장 범위</dt>
                  <dd className="font-black">{formData.is_shared ? '공유' : '개인'}</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="font-bold text-muted-foreground">결과</dt>
                  <dd className="font-black">{testResult ? '실행됨' : '대기'}</dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </section>

        {error && (
          <Card role="alert" className="border-red-200 bg-red-50 text-red-700 dark:border-red-500/30 dark:bg-red-500/15 dark:text-red-200">
            <CardContent className="flex items-center gap-3 py-4">
              <AlertCircle className="size-5 shrink-0" aria-hidden="true" />
              <p className="font-bold">{error}</p>
            </CardContent>
          </Card>
        )}

        {saveStatus && (
          <Card role="status" aria-live="polite" className="border-green-200 bg-green-50 text-green-700 dark:border-green-500/30 dark:bg-green-500/15 dark:text-green-200">
            <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="size-5 shrink-0" aria-hidden="true" />
                <p className="font-bold">{saveStatus}</p>
              </div>
              <a href="/ai-hub" className="text-sm font-black text-current underline underline-offset-4">
                AI 허브 열기
              </a>
            </CardContent>
          </Card>
        )}

        <section className="grid min-h-0 gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(20rem,0.9fr)]">
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <CardTitle className="font-black">템플릿 작성</CardTitle>
                  <CardDescription className="mt-1">저장 전 제목, 설명, 원본 변수, 공유 범위를 확정합니다.</CardDescription>
                </div>
                <Button onClick={handleSave} disabled={saving || testing} className="font-black">
                  {saving ? <Loader2 className="size-4 animate-spin" aria-hidden="true" data-testid="loader" /> : <Save className="size-4" aria-hidden="true" />}
                  {saving ? '저장 중...' : '프롬프트 저장 (Save)'}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_16rem]">
                <div className="space-y-1.5">
                  <label htmlFor="prompt-title" className="text-sm font-bold">프롬프트 이름</label>
                  <Input
                    id="prompt-title"
                    aria-invalid={!formData.title.trim() && Boolean(error)}
                    placeholder="프롬프트 이름"
                    value={formData.title}
                    onChange={e => setFormField('title', e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <label htmlFor="prompt-scope" className="text-sm font-bold">저장 범위</label>
                  <div id="prompt-scope" className="flex min-h-10 items-center gap-2 rounded-xl border border-border bg-background px-3">
                    <Checkbox
                      id="is_shared"
                      checked={formData.is_shared}
                      onCheckedChange={(checked) => setFormField('is_shared', Boolean(checked))}
                    />
                    <label htmlFor="is_shared" className="text-sm font-bold leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                      워크스페이스에 공유하기
                    </label>
                  </div>
                </div>
              </div>

              <div className="space-y-1.5">
                <label htmlFor="prompt-description" className="text-sm font-bold">설명</label>
                <Input
                  id="prompt-description"
                  placeholder="설명"
                  value={formData.description}
                  onChange={e => setFormField('description', e.target.value)}
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="prompt-content" className="text-sm font-bold">프롬프트 내용</label>
                <Textarea
                  id="prompt-content"
                  aria-describedby="prompt-content-help"
                  className="min-h-[17rem] font-mono text-sm"
                  value={formData.content}
                  onChange={e => setPromptContent(e.target.value)}
                />
                <p id="prompt-content-help" className="text-xs font-semibold text-muted-foreground">
                  변수는 <code className="rounded bg-secondary px-1 py-0.5">{'{{email}}'}</code> 형식으로 작성합니다.
                </p>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-6">
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <CardTitle className="flex items-center gap-2 font-black">
                      <Variable className="size-4 text-primary" aria-hidden="true" />
                      변수 입력
                    </CardTitle>
                    <CardDescription className="mt-1">실행 테스트에 전달되는 원본 값을 확인합니다.</CardDescription>
                  </div>
                  <Badge variant="outline" className="font-black">{promptVariables.length}</Badge>
                </div>
              </CardHeader>
              <CardContent className="grid gap-3">
                {promptVariables.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-border bg-secondary/30 p-4 text-sm font-semibold text-muted-foreground">
                    등록된 변수가 없습니다. 프롬프트 내용에 변수를 추가하면 입력 필드가 생성됩니다.
                  </div>
                ) : (
                  promptVariables.map((variableName) => (
                    <div key={variableName} className="space-y-1.5">
                      <label htmlFor={`prompt-variable-${variableName}`} className="text-sm font-bold">
                        {`{{${variableName}}}`}
                      </label>
                      <Textarea
                        id={`prompt-variable-${variableName}`}
                        className="min-h-24"
                        placeholder={`${variableName} 변수 값`}
                        value={getOwnVariableValue(variableValues, variableName) ?? ''}
                        onChange={(event) => {
                          const value = event.target.value;
                          setVariableValues((current) => {
                            const nextValues = createVariableValueMap(Object.entries(current));
                            nextValues[variableName] = value;
                            return nextValues;
                          });
                          setError(null);
                        }}
                      />
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 font-black">
                  <FileText className="size-4 text-primary" aria-hidden="true" />
                  실행 미리보기
                </CardTitle>
                <CardDescription>변수 값이 반영된 요청 본문입니다.</CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="max-h-56 overflow-auto whitespace-pre-wrap rounded-xl border border-border bg-secondary/30 p-4 font-mono text-xs leading-5 text-foreground">
                  {previewText || '프롬프트 내용이 비어 있습니다.'}
                </pre>
              </CardContent>
              <CardFooter className="justify-end">
                <Button onClick={handleTest} disabled={testing || saving || !formData.content.trim()} className="font-black">
                  {testing ? <Loader2 className="size-4 animate-spin" aria-hidden="true" data-testid="loader" /> : <Play className="size-4" aria-hidden="true" />}
                  {testing ? '테스트 중...' : '실행 (Test)'}
                </Button>
              </CardFooter>
            </Card>
          </div>
        </section>

        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle className="font-black">실행 결과</CardTitle>
                <CardDescription className="mt-1">테스트 결과는 저장 전 품질 검토와 Publisher 확인에 사용됩니다.</CardDescription>
              </div>
              <a
                href="/ai-hub"
                className="inline-flex h-10 items-center gap-2 rounded-xl border border-border bg-background px-4 text-sm font-black text-foreground transition-colors hover:border-primary/30 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
              >
                <Share2 className="size-4" aria-hidden="true" />
                AI 허브에서 보기
              </a>
            </div>
          </CardHeader>
          <CardContent>
            <div
              role={testResult ? 'status' : undefined}
              aria-live="polite"
              className="min-h-36 rounded-xl border border-border bg-card p-4 text-sm leading-6"
            >
              {testResult ? (
                <p className="whitespace-pre-wrap">{testResult}</p>
              ) : (
                <div className="flex h-full min-h-28 flex-col items-center justify-center text-center text-muted-foreground">
                  <Sparkles className="mb-3 size-6 text-primary" aria-hidden="true" />
                  <p className="font-black text-foreground">아직 실행 전입니다.</p>
                  <p className="mt-1 max-w-md text-sm">
                    변수 값을 확인하고 실행하면 결과가 이 영역에 표시됩니다.
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
