import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Droplet, RefreshCw } from 'lucide-react';
import { useScanHistory, type ScanHistoryRow } from '../hooks/useScanHistory';

const GRID_SIZE = 5;

interface CellSummary {
  total: number;
  diseased: number;
  lastAt: string | null;
}

function summarize(rows: ScanHistoryRow[]): CellSummary[][] {
  const grid: CellSummary[][] = Array.from({ length: GRID_SIZE }, () =>
    Array.from({ length: GRID_SIZE }, () => ({ total: 0, diseased: 0, lastAt: null }))
  );
  for (const r of rows) {
    if (r.grid_row == null || r.grid_col == null) continue;
    if (r.grid_row < 0 || r.grid_row >= GRID_SIZE) continue;
    if (r.grid_col < 0 || r.grid_col >= GRID_SIZE) continue;
    const cell = grid[r.grid_row][r.grid_col];
    cell.total += 1;
    if (r.is_diseased === true) cell.diseased += 1;
    if (!cell.lastAt || r.created_at > cell.lastAt) cell.lastAt = r.created_at;
  }
  return grid;
}

function cellClasses(cell: CellSummary, selected: boolean): string {
  const base =
    'aspect-square rounded-md flex flex-col items-center justify-center text-xs font-medium transition select-none';
  const ring = selected ? ' ring-2 ring-amber-300' : ' ring-1 ring-zinc-700';
  if (cell.total === 0) return `${base}${ring} bg-zinc-800/60 text-zinc-500`;
  if (cell.diseased > 0) return `${base}${ring} bg-rose-900/60 text-rose-100`;
  return `${base}${ring} bg-emerald-900/60 text-emerald-100`;
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString();
}

function rowLabel(r: ScanHistoryRow): string {
  if (r.grid_row != null && r.grid_col != null) return `R${r.grid_row}C${r.grid_col}`;
  return '—';
}

export default function ScanHistory() {
  const [selected, setSelected] = useState<{ row: number; col: number } | null>(null);

  // Pull a wide set for the heatmap; the filtered list is a separate query.
  const all = useScanHistory({});
  const filtered = useScanHistory(
    selected ? { row: selected.row, col: selected.col } : {}
  );

  const grid = useMemo(() => summarize(all.rows), [all.rows]);
  const listRows = selected ? filtered.rows : all.rows;
  const listLoading = selected ? filtered.loading : all.loading;

  return (
    <div
      className="mx-auto flex min-h-dvh w-full max-w-md flex-col px-5 pt-6"
      style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 1.25rem)' }}
    >
      <header className="flex items-center justify-between">
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-sm text-zinc-400 hover:text-zinc-200"
        >
          <ArrowLeft className="h-4 w-4" /> Back
        </Link>
        <h1 className="text-lg font-semibold tracking-tight text-zinc-100">
          Scan History
        </h1>
        <button
          type="button"
          onClick={() => {
            all.refresh();
            if (selected) filtered.refresh();
          }}
          className="text-zinc-400 hover:text-zinc-200"
          aria-label="Refresh"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </header>

      <section className="mt-5">
        <div className="grid grid-cols-5 gap-1.5">
          {grid.map((cols, r) =>
            cols.map((cell, c) => {
              const isSelected = selected?.row === r && selected?.col === c;
              return (
                <button
                  key={`${r}-${c}`}
                  type="button"
                  onClick={() =>
                    setSelected(isSelected ? null : { row: r, col: c })
                  }
                  className={cellClasses(cell, isSelected)}
                  title={
                    cell.total
                      ? `R${r}C${c} • ${cell.total} scan${cell.total === 1 ? '' : 's'}, ${cell.diseased} diseased`
                      : `R${r}C${c} • no scans`
                  }
                >
                  <span className="text-[10px] text-zinc-300/80">R{r}C{c}</span>
                  <span className="text-base leading-none">{cell.total || '·'}</span>
                </button>
              );
            })
          )}
        </div>
        <p className="mt-2 text-center text-xs text-zinc-500">
          {selected
            ? `Filtering R${selected.row}C${selected.col} — tap again to clear`
            : 'Tap a cell to filter the list below'}
        </p>
      </section>

      <section className="mt-5 flex-1">
        <h2 className="mb-2 text-sm font-medium text-zinc-300">
          {selected ? 'Cell scans' : 'Recent scans'}
        </h2>
        {listLoading && listRows.length === 0 ? (
          <p className="text-sm text-zinc-500">Loading…</p>
        ) : listRows.length === 0 ? (
          <p className="text-sm text-zinc-500">No scans yet.</p>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {listRows.map((r) => {
              const conf =
                r.confidence != null ? `${Math.round(r.confidence * 100)}%` : '—';
              const labelTone =
                r.label === 'error'
                  ? 'text-amber-300'
                  : r.is_diseased
                    ? 'text-rose-300'
                    : r.is_diseased === false
                      ? 'text-emerald-300'
                      : 'text-zinc-300';
              return (
                <li
                  key={r.id}
                  className="rounded-md bg-zinc-900/60 px-3 py-2 ring-1 ring-zinc-800"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-zinc-400">{formatTime(r.created_at)}</span>
                    <span className="font-mono text-zinc-500">{rowLabel(r)}</span>
                  </div>
                  <div className="mt-1 flex items-center justify-between">
                    <span className={`text-sm font-medium ${labelTone}`}>
                      {r.label ?? 'unknown'} · {conf}
                    </span>
                    {r.sprayed ? (
                      <span className="inline-flex items-center gap-1 text-xs text-sky-300">
                        <Droplet className="h-3 w-3" /> sprayed
                      </span>
                    ) : null}
                  </div>
                  {r.notes ? (
                    <p className="mt-1 line-clamp-2 text-xs text-zinc-500">{r.notes}</p>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
