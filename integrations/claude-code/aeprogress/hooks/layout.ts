// Width math for the pane and the band: every row is laid out to fit one line of the
// cells the surface gives, with no `$` in it.

/** Widest a row grows: past this the bars stop stretching and the block stays readable. */
export const MEASURE = 72

// East Asian wide and fullwidth letters and the emoji blocks take two cells.
const WIDE =
  /[\u{1100}-\u{115f}\u{2e80}-\u{303e}\u{3041}-\u{33ff}\u{3400}-\u{4dbf}\u{4e00}-\u{9fff}\u{a000}-\u{a4cf}\u{ac00}-\u{d7a3}\u{f900}-\u{faff}\u{fe30}-\u{fe4f}\u{ff00}-\u{ff60}\u{ffe0}-\u{ffe6}\u{1f300}-\u{1f64f}\u{1f900}-\u{1f9ff}\u{20000}-\u{3fffd}]/u
// Combining marks, zero-width spaces and joiners, and variation selectors take none.
const ZERO = /[\p{M}\u{200b}-\u{200f}\u{fe00}-\u{fe0f}]/u

function charCells(ch: string): number {
  if (ZERO.test(ch)) return 0
  return WIDE.test(ch) ? 2 : 1
}

/** How many terminal cells a text takes: wide (CJK, emoji) letters two, marks none. */
export function cells(text: string): number {
  let n = 0
  for (const ch of text) n += charCells(ch)
  return n
}

/** The text cut to `width` cells, a single `…` marking the cut. */
export function cut(text: string, width: number): string {
  if (width <= 0) return ''
  if (cells(text) <= width) return text
  let out = ''
  let used = 0
  for (const ch of text) {
    const w = charCells(ch)
    if (used + w > width - 1) break
    out += ch
    used += w
  }
  return `${out.trimEnd()}…`
}

/** The first candidate that fits, or the last one cut to fit. */
export function fitFirst(candidates: readonly string[], width: number): string {
  for (const c of candidates) if (cells(c) <= width) return c
  return cut(candidates[candidates.length - 1] ?? '', width)
}

function padEnd(text: string, width: number): string {
  return text + ' '.repeat(Math.max(0, width - cells(text)))
}

function padStart(text: string, width: number): string {
  return ' '.repeat(Math.max(0, width - cells(text))) + text
}

/** The cells a pane row may take: the body less the pane's side padding, up to the measure. */
export function paneWidth(bodyColumns: number, padding: number): number {
  return Math.max(8, Math.min(MEASURE, Math.floor(bodyColumns) - padding * 2))
}

/** One styled run of a row. */
export type Seg = {
  text: string
  color?: 'claude' | 'success' | 'warning' | 'error' | 'suggestion' | 'inactive' | 'subtle'
  dim?: boolean
  bold?: boolean
}

export function segWidth(segs: readonly Seg[]): number {
  return segs.reduce((n, s) => n + cells(s.text), 0)
}

/**
 * A thin bar in half cells: `━` done, `╸` half a cell, `─` the rest. Above 0 it shows at
 * least half a cell and below 1 it never fills, so a nearly done phase never reads done.
 */
export function barParts(fraction: number, width: number): { done: string; rest: string } {
  const w = Math.max(0, width)
  const f = Math.max(0, Math.min(1, fraction))
  let halves = Math.round(f * w * 2)
  if (f > 0 && halves === 0) halves = 1
  if (f < 1 && halves >= w * 2) halves = w * 2 - 1
  const full = Math.floor(halves / 2)
  const done = '━'.repeat(full) + (halves % 2 === 1 ? '╸' : '')
  return { done, rest: '─'.repeat(Math.max(0, w - cells(done))) }
}

/** The header: the run's name on the left, the overall percentage kept whole on the right. */
export function header(runName: string, whole: string, width: number): { left: string; right: string } {
  const room = width - cells(whole) - 2
  const name = runName ? ` · ${runName}` : ''
  const left = fitFirst([`AEP progress${name}`, `AEP${name}`, 'AEP'], room)
  return { left, right: whole }
}

export type PhaseInput = {
  id: string
  title: string
  fraction: number
  approved: number
  total: number
  /** The phase's percentage, as the pane prints percentages. */
  percent: string
  /** Whether the phase is expanded: its disclosure mark points down. */
  open?: boolean
}

export type PhaseRow = Seg[]

const GAP = 2
// A bar never gets narrower than this; a count keeps its percentage only while the bar
// keeps the wider one.
const MIN_BAR = 6
const ROOMY_BAR = 10

/** The disclosure mark of a phase row and the cells it takes. */
const MARK = 2

/**
 * One row per phase: a disclosure mark, id and title, a bar, the count right-aligned.
 * Titles, bars and counts line up in columns; the count drops its percentage before a
 * title is cut short.
 */
export function phaseRows(phases: readonly PhaseInput[], fullWidth: number): PhaseRow[] {
  const width = fullWidth - MARK
  const labels = phases.map(p => `${p.id} ${p.title || 'untitled'}`)
  const longest = Math.max(0, ...labels.map(cells))
  const broken = phases.filter(p => p.total > 0)
  const formats: ((p: PhaseInput) => string)[] = [
    p => `${p.approved}/${p.total} · ${p.percent}`,
    p => `${p.approved}/${p.total} ${p.percent}`,
    p => `${p.approved}/${p.total}`,
  ]
  // The ✓ of a finished phase takes its own column, so every count ends at one edge.
  const tick = phases.some(p => p.total > 0 && p.fraction >= 1) ? 2 : 0
  const titleWish = Math.min(longest, Math.max(12, Math.floor(width * 0.42)))
  let format = formats[formats.length - 1]!
  let countW = 0
  for (const f of formats) {
    const w = Math.max(0, ...broken.map(p => cells(f(p)))) + tick
    format = f
    countW = w
    if (width - w - GAP * 2 - ROOMY_BAR >= Math.min(titleWish, 14)) break
  }
  const titleW = Math.max(4, Math.min(titleWish, width - countW - GAP * 2 - MIN_BAR))
  const barW = Math.max(1, width - titleW - countW - GAP * 2)

  return phases.map((p, i) => {
    const label = cut(labels[i]!, titleW)
    const idPart = label.startsWith(`${p.id} `) ? p.id : label
    const titlePart = label.slice(idPart.length)
    const lead: Seg[] = [
      { text: p.open ? '▾ ' : '▸ ', color: 'inactive' },
      { text: idPart, bold: true },
      { text: padEnd(titlePart, titleW - cells(idPart)) },
    ]
    const spacer: Seg = { text: ' '.repeat(GAP) }
    if (p.total === 0) {
      const room = barW + GAP + countW
      const note = ['not broken down', 'no tasks yet'].find(n => cells(n) <= room) ?? '┄'.repeat(barW)
      return [...lead, spacer, { text: note, color: 'inactive' }]
    }
    const done = p.fraction >= 1
    const { done: filled, rest } = barParts(p.fraction, barW)
    const count = padStart(format(p), countW - tick)
    return [
      ...lead,
      spacer,
      { text: filled, color: done ? 'success' : 'claude' },
      { text: rest, color: 'subtle' },
      spacer,
      { text: count, dim: !done, color: done ? 'success' : undefined },
      ...(tick ? [{ text: done ? ' ✓' : '  ', color: 'success' as const }] : []),
    ]
  })
}

/**
 * The bar and count of an expanded phase, on a line of their own: the count as long as
 * leaves the bar its roomy width, the bar the rest.
 */
export function phaseBarLine(p: PhaseInput, width: number): Seg[] {
  if (p.total === 0) return [{ text: fitFirst(['not broken down into tasks yet', 'not broken down', 'no tasks yet'], width), color: 'inactive' }]
  const done = p.fraction >= 1
  const count = [
    `${p.approved}/${p.total} approved · ${p.percent}`,
    `${p.approved}/${p.total} · ${p.percent}`,
    `${p.approved}/${p.total}`,
  ].find(c => width - cells(c) - GAP >= ROOMY_BAR) ?? `${p.approved}/${p.total}`
  const barW = Math.max(1, width - cells(count) - GAP)
  const { done: filled, rest } = barParts(p.fraction, barW)
  return [
    { text: filled, color: done ? 'success' : 'claude' },
    { text: rest, color: 'subtle' },
    { text: ' '.repeat(GAP) },
    { text: count, dim: !done, color: done ? 'success' : undefined },
  ]
}

/** A task or gate as a chip: a state glyph, the short ID, and who works on it when someone does. */
export type Chip = { glyph: string; color: NonNullable<Seg['color']>; id: string; who?: string }

const WHO_CELLS = 12

/**
 * The chip of an item: approved ✓, conditional ◐, in progress (a live worker) ●,
 * awaiting audit ◌, pending ○, rejected, failed, blocked or conflict ✗. Inside its
 * phase the ID drops the phase (`P2-T3` is `T3`).
 */
export function chipOf(id: string, state: string, who: string | undefined): Chip {
  const short = id.replace(/^P\d+-/i, '')
  if (state === 'APPROVED') return { glyph: '✓', color: 'success', id: short }
  if (who !== undefined) return { glyph: '●', color: 'warning', id: short, who: cut(who, WHO_CELLS) }
  if (state === 'CONDITIONAL') return { glyph: '◐', color: 'error', id: short }
  if (state === 'AWAITING AUDIT') return { glyph: '◌', color: 'suggestion', id: short }
  if (state === 'PENDING') return { glyph: '○', color: 'inactive', id: short }
  return { glyph: '✗', color: 'error', id: short }
}

function chipText(c: Chip): string {
  return `${c.glyph} ${c.id}${c.who ? ` ${c.who}` : ''}`
}

/**
 * Chips packed several to a line, two cells apart, no line wider than `width`. Past
 * `maxLines` the last line ends with `…+N`, N the chips left out.
 */
export function chipLines(chips: readonly Chip[], width: number, maxLines = 2): Seg[][] {
  const lines: Chip[][] = []
  let line: Chip[] = []
  let used = 0
  for (const c of chips) {
    const w = cells(chipText(c))
    const need = line.length === 0 ? w : used + 2 + w
    if (line.length > 0 && need > width) {
      lines.push(line)
      line = []
      used = 0
    }
    line.push(c)
    used = line.length === 1 ? w : used + 2 + w
  }
  if (line.length > 0) lines.push(line)
  let shown = lines
  let left = 0
  if (lines.length > maxLines) {
    shown = lines.slice(0, maxLines)
    left = chips.length - shown.reduce((n, l) => n + l.length, 0)
    const last = shown[shown.length - 1]!
    // Make room for the `…+N` at the end of the last line shown.
    for (;;) {
      const more = `…+${left}`
      const lineW = last.reduce((n, c, i) => n + (i === 0 ? 0 : 2) + cells(chipText(c)), 0)
      if (last.length === 0 || lineW + 2 + cells(more) <= width) break
      last.pop()
      left += 1
    }
  }
  return shown.map((l, n) => {
    const segs: Seg[] = []
    l.forEach((c, i) => {
      if (i > 0) segs.push({ text: '  ' })
      segs.push({ text: `${c.glyph} `, color: c.color }, { text: c.id })
      if (c.who) segs.push({ text: ` ${c.who}`, dim: true })
    })
    if (left > 0 && n === shown.length - 1) segs.push({ text: `${l.length > 0 ? '  ' : ''}…+${left}`, dim: true })
    return segs
  })
}

/** The line under the overall bar: how the percentage is weighed, as much as fits. */
export function weighingLine(phaseCount: number, weighted: boolean, width: number): string {
  const n = `${phaseCount} ${phaseCount === 1 ? 'phase' : 'phases'}`
  const how = weighted ? 'weighted by the plan' : 'equal weights'
  return fitFirst(
    [`${n} · ${how} · only APPROVED closes`, `${n} · ${how}`, `${n} · ${weighted ? 'weighted' : 'equal'}`, n],
    width,
  )
}

/** A list row: `● ID  main · tail`, the main part cut first, the ID never. */
export function listRow(id: string, main: string, tail: string, width: number): { main: string; tail: string } {
  const fixed = 2 + cells(id) + 2
  const tailPart = tail ? ` · ${tail}` : ''
  const room = width - fixed
  if (cells(main) + cells(tailPart) <= room) return { main, tail: tailPart }
  if (cells(tailPart) + 4 <= room) return { main: cut(main, room - cells(tailPart)), tail: tailPart }
  return { main: cut(main + tailPart, room), tail: '' }
}

export type FooterInput = {
  /** Machine busy as a whole percent, or undefined when unknown. */
  busy?: number
  detail?: string
  limit?: { live: number; maxWorkers: number; builds: number; maxBuilds: number; maxBusy: number }
}

/**
 * The machine and launch-limit footer: the mockup's single line when it fits, else the
 * machine and the limit on lines of their own; a dim line under it carries the details.
 */
export function footerRows(input: FooterInput, width: number): { lines: string[]; detail: string } {
  const machine = input.busy === undefined ? 'Machine load unknown' : `Machine ${input.busy}% busy`
  const short = input.busy === undefined ? 'Load unknown' : `Machine ${input.busy}%`
  const lim = input.limit
  const workers = lim ? `workers ${lim.live}/${lim.maxWorkers}` : ''
  const building = lim ? `building ${lim.builds}/${lim.maxBuilds}` : ''
  const dot = 2
  let lines: string[]
  if (!lim) {
    lines = [fitFirst([machine, short], width - dot)]
  } else {
    const builds = `builds ${lim.builds}/${lim.maxBuilds}`
    const one = [
      `${machine}   ${workers}   ${building}`,
      `${short}   ${workers}   ${builds}`,
      `${short}  ${workers}  ${builds}`,
    ].find(c => cells(c) <= width - dot)
    lines = one
      ? [one]
      : [
          fitFirst([machine, short], width - dot),
          fitFirst(
            [`Launch limit  ${workers}  ${builds}`, `${workers}  ${builds}`, `workers ${lim.live}/${lim.maxWorkers}`],
            width - dot,
          ),
        ]
  }
  const held = lim ? Math.round(lim.maxBusy * 100) : 0
  const base = input.detail ?? ''
  const join = (a: string, b: string) => (a && b ? `${a} · ${b}` : a || b)
  const detail = fitFirst(
    lim
      ? [
          join(base, `launch limit holds builds above ${held}%`),
          join(base, `builds held above ${held}%`),
          join(base, `build cap ${held}%`),
          base || `build cap ${held}%`,
        ]
      : [base],
    width - dot,
  )
  return { lines, detail: detail.charAt(0).toUpperCase() + detail.slice(1) }
}

/** The read-time footer, as much of the file's name as fits. */
export function readLine(runName: string, time: string, width: number): string {
  return fitFirst(
    [`Read from ${runName}/compliance-log.md at ${time}`, `Read at ${time} from ${runName}`, `Read at ${time}`],
    width,
  )
}

/** The band's words and buttons, the longest set that fits in one line. */
export function bandLayout(
  secondsLeft: number | null,
  width: number,
): { text: string; seconds: string; cancel: string; now?: string } {
  // A terminal Button is `[ label ]`: four cells around its label, one cell between two.
  const button = (label: string) => cells(label) + 4
  if (secondsLeft === null) {
    const cancel = 'Cancel'
    const text = fitFirst(
      ['Compaction scheduled for the end of this turn', 'Compacting when this turn ends', 'Compacts after this turn', 'After this turn'],
      width - button(cancel) - 1,
    )
    return { text, seconds: '', cancel }
  }
  const seconds = `${secondsLeft}s`
  const options: [string, string, string][] = [
    ['Compacting in ', 'Cancel', 'Compact now'],
    ['Compacting in ', 'Cancel', 'Now'],
    ['Compact in ', 'Cancel', 'Now'],
    ['In ', 'Cancel', 'Now'],
    ['', 'Cancel', 'Now'],
  ]
  for (const [lead, cancel, now] of options) {
    if (cells(lead) + cells(seconds) + 1 + button(cancel) + 1 + button(now) <= width) return { text: lead, seconds, cancel, now }
  }
  return { text: '', seconds, cancel: 'Cancel', now: 'Now' }
}
