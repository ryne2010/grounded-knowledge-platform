import { cn } from '../lib/utils'

export type SpinnerProps = {
  /**
   * Visual size of the spinner.
   *
   * Keep this tiny and dependency-free so `portfolio-ui` can be reused across repos.
   */
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const SIZE: Record<NonNullable<SpinnerProps['size']>, string> = {
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
  lg: 'h-6 w-6',
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={cn(
        'inline-block animate-spin rounded-full border-2 border-border border-t-foreground',
        SIZE[size],
        className,
      )}
    />
  )
}
