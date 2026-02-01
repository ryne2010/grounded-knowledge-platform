import * as React from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { cn } from '../lib/utils'

type ColumnMeta = {
  headerClassName?: string
  cellClassName?: string
  width?: number
  minWidth?: number
  maxWidth?: number
}

export type DataTableProps<T> = {
  data: T[]
  columns: ColumnDef<T, any>[]
  height?: number
  className?: string
  /**
   * Optional row class hook to highlight rows (e.g., cited chunks, alerts).
   * Keep this UI-only so it can be shared via git subtree without backend coupling.
   */
  getRowClassName?: (row: T) => string
}

export function DataTable<T>(props: DataTableProps<T>) {
  const parentRef = React.useRef<HTMLDivElement>(null)

  const table = useReactTable({
    data: props.data,
    columns: props.columns,
    getCoreRowModel: getCoreRowModel(),
  })

  const rows = table.getRowModel().rows

  const gridTemplateColumns = React.useMemo(() => {
    return table.getVisibleLeafColumns().map((col) => {
      const meta = col.columnDef.meta as ColumnMeta | undefined
      if (meta?.width != null) return `${meta.width}px`
      if (meta?.minWidth != null || meta?.maxWidth != null) {
        const min = meta?.minWidth ?? 0
        const max = meta?.maxWidth
        return max != null ? `minmax(${min}px, ${max}px)` : `minmax(${min}px, 1fr)`
      }
      return 'minmax(0, 1fr)'
    }).join(' ')
  }, [table])

  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 44,
    // Measure actual row height so wrapped cells don't overlap.
    measureElement: (el) => el.getBoundingClientRect().height,
    overscan: 10,
  })

  return (
    <div
      ref={parentRef}
      className={cn(
        'rounded-md border bg-card text-card-foreground',
        'overflow-auto',
        props.className,
      )}
      style={{ height: props.height ?? 520 }}
    >
      <table className="w-full text-sm">
        <thead className="sticky top-0 z-10 bg-card">
          {table.getHeaderGroups().map((hg) => (
            <tr
              key={hg.id}
              className="grid border-b"
              style={{ gridTemplateColumns }}
            >
              {hg.headers.map((header) => (
                <th
                  key={header.id}
                  className={cn(
                    'px-4 py-2 text-left font-medium text-muted-foreground',
                    (header.column.columnDef.meta as ColumnMeta | undefined)?.headerClassName,
                  )}
                  style={{
                    width: (header.column.columnDef.meta as ColumnMeta | undefined)?.width,
                    minWidth: (header.column.columnDef.meta as ColumnMeta | undefined)?.minWidth,
                    maxWidth: (header.column.columnDef.meta as ColumnMeta | undefined)?.maxWidth,
                  }}
                >
                  {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody
          className="relative"
          style={{ height: rowVirtualizer.getTotalSize() }}
        >
          {rowVirtualizer.getVirtualItems().map((virtualRow) => {
            const row = rows[virtualRow.index]
            const extraRowClass = props.getRowClassName ? props.getRowClassName(row.original as T) : ''
            return (
              <tr
                key={row.id}
                data-index={virtualRow.index}
                ref={rowVirtualizer.measureElement}
                className={cn(
                  'absolute left-0 right-0 grid border-b last:border-b-0 hover:bg-accent/50',
                  extraRowClass,
                )}
                style={{
                  transform: `translateY(${virtualRow.start}px)`,
                  gridTemplateColumns,
                }}
              >
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className={cn(
                      'px-4 py-2 align-middle',
                      (cell.column.columnDef.meta as ColumnMeta | undefined)?.cellClassName,
                    )}
                    style={{
                      width: (cell.column.columnDef.meta as ColumnMeta | undefined)?.width,
                      minWidth: (cell.column.columnDef.meta as ColumnMeta | undefined)?.minWidth,
                      maxWidth: (cell.column.columnDef.meta as ColumnMeta | undefined)?.maxWidth,
                    }}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
