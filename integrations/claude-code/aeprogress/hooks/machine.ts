// How busy the machine is, read from whatever the system offers: the mod API does not
// name the operating system, so each source is tried by what exists.
import type { EngineInterface } from 'claude-code'

import type { Machine } from '../types'

const STEP_TIMEOUT_MS = 3_000
const POWERSHELL_TIMEOUT_MS = 8_000
// The processes macOS runs to index files for Spotlight.
const INDEXER = /\b(corespotlightd|mds_stores|mdworker_shared|mdworker)\b/

function numbers(text: string): number[] {
  return text.match(/[0-9]+(?:[.,][0-9]+)?/g)?.map(n => Number(n.replace(',', '.'))) ?? []
}

/** Linux: the 1-minute load from /proc/loadavg over the processors /proc/cpuinfo lists. */
export function linuxMachine(loadavg: string, cpuinfo: string): Machine | undefined {
  const load = numbers(loadavg)[0]
  const cores = (cpuinfo.match(/^processor\s*:/gm) ?? []).length
  if (load === undefined || cores === 0) return undefined
  return { busy: load / cores, detail: `load ${load.toFixed(1)} of ${cores} cores`, os: 'linux', indexerCpu: 0 }
}

/** macOS and the BSDs: `sysctl -n vm.loadavg` ("{ 2.31 2.05 1.90 }") over `sysctl -n hw.ncpu`. */
export function sysctlMachine(loadavg: string, ncpu: string, os: 'macos' | 'bsd', ps = ''): Machine | undefined {
  const load = numbers(loadavg)[0]
  const cores = numbers(ncpu)[0]
  if (load === undefined || !cores) return undefined
  return { busy: load / cores, detail: `load ${load.toFixed(1)} of ${cores} cores`, os, indexerCpu: indexerCpu(ps) }
}

/** Windows has no load average: the processors' average LoadPercentage stands in. */
export function windowsMachine(percentOut: string): Machine | undefined {
  const cpu = numbers(percentOut)[0]
  if (cpu === undefined) return undefined
  return { busy: cpu / 100, detail: `CPU at ${Math.round(cpu)}%`, os: 'windows', indexerCpu: 0 }
}

/** CPU % of Spotlight's indexing processes in `ps -A -o %cpu=,comm=` output, added up. */
export function indexerCpu(ps: string): number {
  let total = 0
  for (const line of ps.split('\n')) {
    if (INDEXER.test(line)) total += Number.parseFloat(line.trim().replace(',', '.')) || 0
  }
  return total
}

async function run($: EngineInterface, argv: string[], timeoutMs = STEP_TIMEOUT_MS): Promise<string | undefined> {
  const ran = await $.process.run(argv, { timeoutMs }).catch(() => undefined)
  return ran && ran.exitCode === 0 ? ran.stdout : undefined
}

/** The machine's load now, or undefined when no source answers. Never throws. */
export async function readMachine($: EngineInterface): Promise<Machine | undefined> {
  try {
    if (await $.fs.exists('/proc/loadavg')) {
      const loadavg = (await $.fs.read('/proc/loadavg')) as string
      const cpuinfo = ((await $.fs.read('/proc/cpuinfo').catch(() => '')) as string) || ''
      const fromProc = linuxMachine(loadavg, cpuinfo)
      if (fromProc) return fromProc
      // A /proc/cpuinfo without "processor" lines (some ARM boards): ask nproc.
      const nproc = await run($, ['nproc'])
      return nproc ? linuxMachine(loadavg, 'processor :\n'.repeat(numbers(nproc)[0] ?? 0)) : undefined
    }
    for (const sysctl of ['/usr/sbin/sysctl', '/sbin/sysctl']) {
      if (!(await $.fs.exists(sysctl))) continue
      const isMac = await $.fs.exists('/System/Library/CoreServices')
      const loadavg = (await run($, [sysctl, '-n', 'vm.loadavg'])) ?? ''
      const ncpu = (await run($, [sysctl, '-n', 'hw.ncpu'])) ?? ''
      // Spotlight only exists on macOS; nowhere else is ps run for it.
      const ps = isMac ? ((await run($, ['/bin/ps', '-A', '-o', '%cpu=,comm='])) ?? '') : ''
      return sysctlMachine(loadavg, ncpu, isMac ? 'macos' : 'bsd', ps)
    }
    if ((await $.env.get('SystemRoot')) || (await $.env.get('WINDIR'))) {
      const out = await run(
        $,
        [
          'powershell',
          '-NoProfile',
          '-Command',
          '(Get-CimInstance Win32_Processor | Measure-Object LoadPercentage -Average).Average',
        ],
        POWERSHELL_TIMEOUT_MS,
      )
      return out ? windowsMachine(out) : undefined
    }
  } catch {
    // Falls through: the load is unknown.
  }
  return undefined
}
