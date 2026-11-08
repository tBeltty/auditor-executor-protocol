// Whether a newer version exists: the version arithmetic and where a copy runs from. The
// check itself, with `$`, is in register.tsx.

export type UpdateMode = 'on' | 'off'
export type InstallKind = 'synced' | 'marketplace' | 'local'

/** "0.3.4" -> [0, 3, 4]; anything else is undefined. */
export function versionParts(version: string): number[] | undefined {
  const m = version.trim().match(/^v?(\d+)\.(\d+)\.(\d+)$/)
  return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : undefined
}

export function isNewer(candidate: string, current: string): boolean {
  const a = versionParts(candidate)
  const b = versionParts(current)
  if (!a || !b) return false
  for (let i = 0; i < 3; i++) if (a[i] !== b[i]) return (a[i] ?? 0) > (b[i] ?? 0)
  return false
}

/**
 * How this copy was installed, read from where it runs: synced from claude.ai (the
 * directory, which updates it at each start), copied from a marketplace, or a folder
 * loaded in place (`--plugin-dir`, a local marketplace).
 */
export function installKind(root: string): InstallKind {
  const path = root.replace(/\\/g, '/')
  if (/\/plugins\/synced\//.test(path)) return 'synced'
  if (/\/plugins\/cache\/[^/]+\/[^/]+\/[^/]+\/?$/.test(path)) return 'marketplace'
  return 'local'
}

/** The marketplace clone a cached copy came from: plugins/cache/<m>/... -> plugins/marketplaces/<m>. */
export function marketplaceDir(root: string): string | undefined {
  const m = root.replace(/\\/g, '/').match(/^(.*\/plugins)\/cache\/([^/]+)\/[^/]+\/[^/]+\/?$/)
  return m ? `${m[1]}/marketplaces/${m[2]}` : undefined
}

export function versionIn(text: string): string | undefined {
  try {
    const version = (JSON.parse(text) as { version?: unknown }).version
    return typeof version === 'string' && versionParts(version) ? version : undefined
  } catch {
    return undefined
  }
}

export function howToUpdate(kind: InstallKind): string {
  return kind === 'marketplace'
    ? 'Update it from /plugin, Installed, auditor-executor-protocol, Update now.'
    : 'Pull the new version where you load it from.'
}

/** The version a marketplace catalog (`marketplace.json`) lists for a plugin, if any. */
export function catalogEntryVersion(catalog: string, plugin: string): string | undefined {
  try {
    const entries = (JSON.parse(catalog) as { plugins?: { name?: string; version?: unknown }[] }).plugins ?? []
    const version = entries.find(p => p.name === plugin)?.version
    return typeof version === 'string' && versionParts(version) ? version : undefined
  } catch {
    return undefined
  }
}
