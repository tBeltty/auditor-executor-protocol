// Whether a newer aeprogress exists: from the marketplace catalog Claude Code keeps on disk
// (no network), and, at most once a day, from the plugin's public manifest on GitHub.
import { atom, read, update } from 'claude-code'
import type { EngineInterface } from 'claude-code'

import type { UpdateInfo } from '../types'

/** The plugin's published manifest; only its `version` is read. */
export const REMOTE_MANIFEST =
  'https://raw.githubusercontent.com/tBeltty/auditor-executor-protocol/main/integrations/claude-code/aeprogress/.claude-plugin/plugin.json'
const DAY_MS = 86_400_000
const FETCH_TIMEOUT_MS = 8_000
const STORE_KEY = 'updateCheck'

export type UpdateMode = 'daily' | 'offline' | 'off'
export type InstallKind = 'synced' | 'marketplace' | 'local'

const available = atom(
  { plugin: 'aeprogress', key: 'updateAvailable' } as const,
  null as UpdateInfo | null,
  { shape: 'update-1' },
)

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

function versionIn(text: string): string | undefined {
  try {
    const version = (JSON.parse(text) as { version?: unknown }).version
    return typeof version === 'string' && versionParts(version) ? version : undefined
  } catch {
    return undefined
  }
}

async function readVersion($: EngineInterface, path: string): Promise<string | undefined> {
  const text = await $.fs.read(path).catch(() => undefined)
  return typeof text === 'string' ? versionIn(text) : undefined
}

/** The version the on-disk marketplace catalog lists, refreshed whenever Claude Code updates it. */
async function catalogVersion($: EngineInterface, root: string): Promise<string | undefined> {
  const dir = marketplaceDir(root)
  if (!dir) return undefined
  const text = await $.fs.read(`${dir}/.claude-plugin/marketplace.json`).catch(() => undefined)
  if (typeof text !== 'string') return undefined
  try {
    const entries = (JSON.parse(text) as { plugins?: { name?: string; source?: unknown }[] }).plugins ?? []
    const source = entries.find(p => p.name === $.plugin.name)?.source
    if (typeof source !== 'string' || !source.startsWith('./')) return undefined
    return readVersion($, `${dir}/${source.slice(2).replace(/\/+$/, '')}/.claude-plugin/plugin.json`)
  } catch {
    return undefined
  }
}

/** The published version, asked of GitHub at most once a day; the answer is kept between sessions. */
async function remoteVersion($: EngineInterface): Promise<string | undefined> {
  if (await $.env.get('CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC')) return undefined
  const now = await $.clock.now()
  const last = (await $.store.get(STORE_KEY).catch(() => undefined)) as { at?: number; version?: string } | undefined
  if (last && typeof last.at === 'number' && now - last.at < DAY_MS) return last.version
  const timeout = $.clock.sleep(FETCH_TIMEOUT_MS).then(() => undefined)
  const response = await Promise.race([$.http.fetch(REMOTE_MANIFEST).catch(() => undefined), timeout])
  const version = response && response.ok ? versionIn(response.text) : undefined
  await $.store.set(STORE_KEY, { at: now, ...(version ? { version } : {}) }).catch(() => undefined)
  return version
}

/** Looks for a newer version and keeps what it found for the pane; never throws. */
export async function checkForUpdate($: EngineInterface, mode: UpdateMode): Promise<void> {
  try {
    if (mode === 'off') return
    const root = $.plugin.root
    const kind = installKind(root)
    if (kind === 'synced') return
    const installed = await readVersion($, `${root}/.claude-plugin/plugin.json`)
    if (!installed) return
    const found = [
      kind === 'marketplace' ? await catalogVersion($, root) : undefined,
      mode === 'daily' ? await remoteVersion($) : undefined,
    ].filter((v): v is string => v !== undefined)
    const latest = found.reduce<string | undefined>((best, v) => (!best || isNewer(v, best) ? v : best), undefined)
    if (!latest || !isNewer(latest, installed)) {
      await update($, available, () => null)
      return
    }
    await update($, available, () => ({ installed, latest, kind }))
    $.ui.toast(`aeprogress ${latest} is available (you have ${installed}). ${howToUpdate(kind)}`)
  } catch {
    // An update check that fails changes nothing.
  }
}

export function howToUpdate(kind: InstallKind): string {
  return kind === 'marketplace'
    ? 'Update it from /plugin, Installed, aeprogress, Update now.'
    : 'Pull the new version where you load it from.'
}

/** What the last check found, read while drawing the pane. */
export async function updateNotice($: EngineInterface): Promise<UpdateInfo | null> {
  return read($, available)
}
