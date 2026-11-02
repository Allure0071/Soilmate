export function authErrorMessage(status, data) {
  if (typeof data?.detail === 'string') return data.detail
  if (status === 422) {
    const issue = Array.isArray(data?.detail) ? data.detail[0] : null
    const field = issue?.loc?.at(-1)
    if (field === 'password') return '密码需为 12～128 个字符，请检查输入；首次使用请先创建账号。'
    if (field === 'email') return '请输入有效的邮箱地址。'
    return '登录信息格式不正确，请检查邮箱和密码。'
  }
  return '登录服务暂时不可用，请稍后重试。'
}
