// Reads a drawn tree back as the lines a terminal paints, to measure each one.
import { cells } from '../hooks/layout'

type Node = string | { type: string; props?: Record<string, unknown>; children?: Node[] }
/** A painted line, and whether it holds prose the surface may wrap (`wrap="wrap"`). */
type Line = { text: string; prose: boolean }

function textOf(node: Node): string {
  if (typeof node === 'string') return node
  return (node.children ?? []).map(textOf).join('')
}

function isProse(node: Node): boolean {
  return typeof node !== 'string' && (node.props?.wrap === 'wrap' || (node.children ?? []).some(isProse))
}

function isPlaced(node: Node): boolean {
  return typeof node !== 'string' && node.type === 'Box' && node.props?.position === 'absolute'
}

function lines(node: Node): Line[] {
  if (typeof node === 'string') return [{ text: node, prose: false }]
  if (node.type === 'Button') {
    // A plain Button draws its children (or its label) bare; any other `[ label ]`.
    const children = node.children ?? []
    const shown = node.props?.plain ? (children.length > 0 ? textOf(node) : String(node.props?.label ?? '')) : `[ ${String(node.props?.label ?? '')} ]`
    return [{ text: shown, prose: children.some(isProse) }]
  }
  if (node.type !== 'Box') return [{ text: textOf(node), prose: isProse(node) }]
  const pad = ' '.repeat(Number(node.props?.paddingX ?? 0))
  const left = ' '.repeat(Number(node.props?.paddingLeft ?? 0))
  const border = node.props?.borderStyle ? '│' : ''
  // A placed Box takes no room among its siblings: it is measured on its own.
  const kids = (node.children ?? []).filter(k => !isPlaced(k))
  const wrap = (l: Line): Line => ({ text: border + left + pad + l.text + pad + border, prose: l.prose })
  if (node.props?.flexDirection === 'column') return kids.flatMap(lines).map(wrap)
  const parts = kids.map(lines)
  return [wrap({ text: parts.map(p => p.map(l => l.text).join('')).join(''), prose: parts.some(p => p.some(l => l.prose)) })]
}

function placed(node: Node): Node[] {
  if (typeof node === 'string') return []
  return [...(isPlaced(node) ? [node] : []), ...(node.children ?? []).flatMap(placed)]
}

/** The lines a tree paints in the flow, placed (absolute) Boxes left out. */
export function linesOf(node: Node): string[] {
  return lines(node).map(l => l.text)
}

/**
 * The lines of a drawing wider than `columns` cells, with their widths; prose rows the
 * surface wraps are left out. A placed card must fit inside the drawing too: its offset
 * and width within `columns`, each of its lines within its width.
 */
export function overflowing(tree: unknown, columns: number, padding = 0): string[] {
  const root = tree as Node
  const flow = lines(root)
    .filter(l => !l.prose && cells(l.text) > columns)
    .map(l => `${cells(l.text)} > ${columns}: ${l.text}`)
  const cards = placed(root).flatMap(node => {
    const card = node as Exclude<Node, string>
    const props = card.props ?? {}
    const width = Number(props.width ?? 0)
    const reach = padding + Number(props.left ?? 0) + width
    const out = reach > columns ? [`card reaches ${reach} > ${columns}`] : []
    const inner = lines({ ...card, props: { ...props, position: 'relative' } })
    return out.concat(inner.filter(l => !l.prose && cells(l.text) > width).map(l => `card line ${cells(l.text)} > ${width}: ${l.text}`))
  })
  return [...flow, ...cards]
}

/** The placed (absolute) Boxes of a drawing: the hover cards. */
export function cardsOf(tree: unknown): unknown[] {
  return placed(tree as Node)
}
