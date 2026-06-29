with open("frontend/src/components/EmailDetail.tsx", "r") as f:
    content = f.read()

# Add state
if "const [translation" not in content:
    state_search = "const [draft, setDraft] = useState<string>('');"
    state_replace = """const [draft, setDraft] = useState<string>('');
  const [translation, setTranslation] = useState<string | null>(null);
  const [isTranslating, setIsTranslating] = useState(false);
  const [translationError, setTranslationError] = useState<string | null>(null);"""
    content = content.replace(state_search, state_replace)

# Add handler
if "const handleTranslate = useCallback" not in content:
    handler_search = "const handleDraftReply = useCallback(async () => {"
    handler_replace = """const handleTranslate = useCallback(async () => {
    if (!email) return;
    const actionEmailId = email.id;
    const isCurrentEmail = () => currentEmailIdRef.current === actionEmailId;
    setIsTranslating(true);
    setTranslationError(null);
    try {
      const data = await apiClient.post<{ translation: string }>('/api/llm/translate', { email_body: email.body, target_language: 'Korean' });
      if (!isCurrentEmail()) return;
      setTranslation(data.translation || null);
    } catch (err) {
      if (!isCurrentEmail()) return;
      console.error("Error translating email:", err);
      setTranslationError("번역을 수행하지 못했습니다.");
    } finally {
      if (isCurrentEmail()) setIsTranslating(false);
    }
  }, [email]);

  const handleDraftReply = useCallback(async () => {"""
    content = content.replace(handler_search, handler_replace)

# Add translate button UI
if "번역 중" not in content:
    ui_search = '<div className="break-words text-lg font-black tracking-tight text-foreground xl:text-xl">{safeEmailSubject}</div>'
    ui_replace = """<div className="flex items-start justify-between gap-4 w-full">
              <div className="break-words text-lg font-black tracking-tight text-foreground xl:text-xl">{safeEmailSubject}</div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleTranslate}
                disabled={isTranslating}
                aria-busy={isTranslating}
                className="shrink-0 rounded-xl px-3 h-8 text-xs font-bold shadow-sm"
              >
                {isTranslating && <Loader2 className="mr-2 h-3 w-3 animate-spin" aria-hidden="true" />}
                {isTranslating ? "번역 중" : "번역"}
              </Button>
            </div>"""
    content = content.replace(ui_search, ui_replace)

# Add translation result UI
if "한국어 번역 결과" not in content:
    ui_result_search = '<div className="text-sm leading-6 whitespace-pre-wrap">{toMailBodyText(msg.body)}</div>'
    ui_result_replace = """{msg.id === email.id && translationError && (
                    <div role="alert" className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600">
                      {translationError}
                    </div>
                  )}
                  {msg.id === email.id && translation && (
                    <div className="mb-6 rounded-2xl bg-secondary/40 p-4 border border-border">
                      <p className="text-xs font-bold text-primary mb-2">한국어 번역 결과</p>
                      <div className="text-sm leading-6 whitespace-pre-wrap">{toMailBodyText(translation)}</div>
                    </div>
                  )}
                  <div className="text-sm leading-6 whitespace-pre-wrap">{toMailBodyText(msg.body)}</div>"""

    # only replace the first occurrence (main body, not thread loop)
    content = content.replace(ui_result_search, ui_result_replace, 1)

with open("frontend/src/components/EmailDetail.tsx", "w") as f:
    f.write(content)
