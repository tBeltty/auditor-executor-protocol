// How busy the machine is: the parsers for what each system prints. Reading it, with `$`,
// is in register.tsx.

import type { Machine } from '../types'

// The processes macOS runs to index files for Spotlight.
const INDEXER = /\b(corespotlightd|mds_stores|mdworker_shared|mdworker)\b/

export function numbers(text: string): number[] {
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
