const { JSDOM } = require('jsdom');
const window = new JSDOM('').window;
global.window = window;
global.document = window.document;
const DOMPurify = require('dompurify');
console.log(DOMPurify.sanitize('<script>문서 원본 검토</script>', { ALLOWED_TAGS: [] }).trim() || '제목 없는 작업');
