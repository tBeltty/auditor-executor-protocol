// Reads a drawn tree back as the lines a terminal paints, to measure each one.
import { cells } from '../hooks/layout'

type Node = string | { type: string; props?: Record<string, unknown>; children?: Node[] }

function textOf(node: Node): string {
  if (typeof node === 'string') return node
  if (node.type === 'Button') return `[ ${String(node.props?.label ?? '')} ]`
  return (node.children ?? []).map(textOf).join('')
}

/**
 * The lines a tree paints: a column Box stacks its children, a row Box (the default)
 * lays them side by side at their narrowest, a Text is one line before any wrapping.
 */
export function linesOf(node: Node): string[] {
  if (typeof node === 'string') return [node]
  if (node.type !== 'Box') return [textOf(node)]
  const pad = ' '.repeat(Number(node.props?.paddingX ?? 0))
  const kids = node.children ?? []
  if (node.props?.flexDirection === 'column') return kids.flatMap(linesOf).map(line => pad + line + pad)
  return [pad + kids.map(k => linesOf(k).join('')).join('') + pad]
}

/** The lines of a drawing wider than `columns` cells, with their widths. */
export function overflowing(tree: unknown, columns: number): string[] {
  return linesOf(tree as Node)
    .filter(line => cells(line) > columns)
    .map(line => `${cells(line)} > ${columns}: ${line}`)
}
