const workspacePaths = new Set(['/analysis', '/evidence', '/assessment', '/research', '/assistant', '/explore', '/resources', '/tools'])

export function accountDestination(nextPath) {
  if (typeof nextPath !== 'string' || !nextPath.startsWith('/') || nextPath.startsWith('//')) return '/research'
  try {
    const target = new URL(nextPath, 'https://soilmate.local')
    if (target.origin === 'https://soilmate.local' && workspacePaths.has(target.pathname)) {
      return target.pathname + target.search + target.hash
    }
  } catch { /* Fall back to the research entry for invalid destinations. */ }
  return '/research'
}
