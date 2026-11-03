export class AssessmentError extends Error {
  constructor(message, details = {}) { super(message); Object.assign(this, details) }
}
export function createAssessmentApi({ csrf = () => '', fetcher = fetch, allowMock = false } = {}) {
  return async (method, path, body, key, signal) => {
    const controller = new AbortController()
    const abort = () => controller.abort()
    signal?.addEventListener('abort', abort, { once: true })
    if (signal?.aborted) abort()
    const timer = setTimeout(abort, 15000)
    try {
      const response = await fetcher('/api/assessment' + path, { method, credentials: 'same-origin', signal: controller.signal, headers: { Accept: 'application/json', ...(body && { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf(), 'Idempotency-Key': key }) }, ...(body && { body: JSON.stringify(body) }) })
      let envelope
      try { envelope = await response.json() } catch { envelope = null }
      if (!response.ok) {
        const messages = { 401: '登录已失效，请重新登录；录入草稿已保留。', 403: '无权访问这条研究记录，请切换到所属账号。', 404: '健康评价接口或记录暂不可用，请稍后重试；录入草稿已保留。', 409: '提交内容或记录版本冲突，请返回核对，勿重复新建任务。', 422: '输入未通过服务端校验，请返回录入页修正。', 429: '分析服务繁忙，请稍后重试。', 503: '分析模型暂不可用，录入草稿已保留。' }
        throw new AssessmentError(messages[response.status] || '分析服务暂时无法完成请求，请稍后重试。', { status: response.status, code: envelope?.error?.code || 'HTTP_ERROR', requestId: envelope?.request_id || '', fields: envelope?.error?.fields || [], retryable: envelope?.error?.retryable ?? [404, 429, 500, 502, 503, 504].includes(response.status) })
      }
      if (!envelope || !['real', 'mock'].includes(envelope.data_origin) || (!allowMock && envelope.data_origin === 'mock') || !envelope.data) throw new AssessmentError('服务返回格式与评价契约不一致，未展示为有效分析结果。', { code: 'INVALID_RESPONSE', retryable: false })
      return { data: envelope.data, origin: envelope.data_origin, requestId: envelope.request_id || '' }
    } catch (error) {
      if (signal?.aborted) throw error
      if (error instanceof AssessmentError) throw error
      throw new AssessmentError('连接中断或等待超时。可继续查询或重试原提交，避免重复创建任务。', { code: 'NETWORK_ERROR', retryable: true })
    } finally { clearTimeout(timer); signal?.removeEventListener('abort', abort) }
  }
}
