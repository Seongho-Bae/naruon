function safeTaskTitle(title) {
  const displayTitle = title
    .replace(/<[^>]*>/g, ' ')
    .replace(/[<>]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return displayTitle || '제목 없는 작업';
}

console.log(safeTaskTitle('<img src=x onerror=alert(1)>문서 원본 검토'));
