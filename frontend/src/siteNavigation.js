export const siteLinks = [
  { id: 'home', label: '首页', href: '/' },
  { id: 'explore', label: '探索数据', href: '/explore' },
  { id: 'gold', label: '数据资源', href: '/resources' },
  { id: 'research', label: '健康研究', href: '/research' },
  { id: 'assistant', label: 'AI 助手', href: '/assistant' },
  { id: 'tools', label: '工具中心', href: '/tools' },
]

export const primaryLinks = siteLinks.filter(link => link.id !== 'home').map(link => ({ ...link, views: [link.id] }))

export function viewFromPath(pathname) {
  if (['/assessment', '/assessment/preview', '/analysis', '/evidence', '/research'].includes(pathname)) return 'research'
  return siteLinks.find(link => link.href === pathname)?.id || 'home'
}
