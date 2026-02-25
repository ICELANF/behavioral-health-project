import DOMPurify from 'dompurify'

/**
 * 安全格式化消息文本 (markdown → HTML + DOMPurify sanitize)
 * 用于所有 v-html 渲染 AI/用户内容的场景，防止 XSS
 */
export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['strong', 'em', 'code', 'br', 'p', 'ul', 'ol', 'li', 'a', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'blockquote', 'pre'],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'class', 'style'],
    ALLOW_DATA_ATTR: false,
  })
}

/**
 * 格式化聊天消息: 简单 markdown → HTML + sanitize
 */
export function formatChatMessage(content: string): string {
  if (!content) return ''
  const html = content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
  return sanitizeHtml(html)
}
