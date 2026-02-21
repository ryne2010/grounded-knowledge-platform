import * as React from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'

import { api, type GcsSyncResponse, type IngestEventView } from '../api'
import { getConnectorAvailability, summarizeGcsSyncRun } from '../lib/gcsConnector'
import { formatUnixSeconds } from '../lib/time'
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Checkbox,
  DataTable,
  Input,
  Label,
  Page,
  Section,
  Spinner,
  Textarea,
} from '../portfolio-ui'

export function IngestPage() {
  const qc = useQueryClient()

  const metaQuery = useQuery({ queryKey: ['meta'], queryFn: api.meta, staleTime: 30_000 })
  const meta = metaQuery.data
  const uploadsEnabled = Boolean(meta?.uploads_enabled)
  const connectorAvailability = getConnectorAvailability(meta)
  const connectorsEnabled = connectorAvailability.enabled
  const authMode = String(meta?.auth_mode ?? 'none')

  function parseTags(raw: string): string[] | undefined {
    const tags = raw
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean)
    return tags.length ? tags : undefined
  }

  // ---- Upload form ----
  const [file, setFile] = React.useState<File | null>(null)
  const [contractFile, setContractFile] = React.useState<File | null>(null)
  const [fileTitle, setFileTitle] = React.useState('')
  const [fileSource, setFileSource] = React.useState('ui:file')
  const [fileClassification, setFileClassification] = React.useState('internal')
  const [fileRetention, setFileRetention] = React.useState('none')
  const [fileTags, setFileTags] = React.useState('')
  const [fileNotes, setFileNotes] = React.useState('')

  const uploadMutation = useMutation({
    mutationFn: api.ingestFile,
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['docs'] })
      await qc.invalidateQueries({ queryKey: ['stats'] })
      await qc.invalidateQueries({ queryKey: ['ingest-events'] })
      await qc.invalidateQueries({ queryKey: ['recent-ingest-events'] })
    },
  })

  // ---- Paste form ----
  const [pasteTitle, setPasteTitle] = React.useState('')
  const [pasteSource, setPasteSource] = React.useState('ui:paste')
  const [pasteClassification, setPasteClassification] = React.useState('internal')
  const [pasteRetention, setPasteRetention] = React.useState('none')
  const [pasteTags, setPasteTags] = React.useState('')
  const [pasteNotes, setPasteNotes] = React.useState('')
  const [pasteText, setPasteText] = React.useState('')

  const pasteMutation = useMutation({
    mutationFn: api.ingestText,
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['docs'] })
      await qc.invalidateQueries({ queryKey: ['stats'] })
      await qc.invalidateQueries({ queryKey: ['ingest-events'] })
      await qc.invalidateQueries({ queryKey: ['recent-ingest-events'] })
    },
  })

  // ---- GCS connector sync ----
  const [gcsBucket, setGcsBucket] = React.useState('')
  const [gcsPrefix, setGcsPrefix] = React.useState('')
  const [gcsMaxObjects, setGcsMaxObjects] = React.useState(200)
  const [gcsDryRun, setGcsDryRun] = React.useState(true)
  const [gcsClassification, setGcsClassification] = React.useState('internal')
  const [gcsRetention, setGcsRetention] = React.useState('none')
  const [gcsTags, setGcsTags] = React.useState('')
  const [gcsNotes, setGcsNotes] = React.useState('')
  const [latestSyncRun, setLatestSyncRun] = React.useState<GcsSyncResponse | null>(null)
  const [syncCopyStatus, setSyncCopyStatus] = React.useState<'idle' | 'copied' | 'failed'>('idle')

  const gcsSyncMutation = useMutation({
    mutationFn: api.gcsSync,
    onSuccess: async (run) => {
      setLatestSyncRun(run)
      setSyncCopyStatus('idle')
      await qc.invalidateQueries({ queryKey: ['docs'] })
      await qc.invalidateQueries({ queryKey: ['stats'] })
      await qc.invalidateQueries({ queryKey: ['ingest-events'] })
      await qc.invalidateQueries({ queryKey: ['recent-ingest-events'] })
    },
  })

  const gcsSummary = React.useMemo(
    () => (latestSyncRun ? summarizeGcsSyncRun(latestSyncRun) : null),
    [latestSyncRun],
  )

  // ---- Ingest events feed ----
  const [q, setQ] = React.useState('')
  const [changedOnly, setChangedOnly] = React.useState(false)

  const eventsQuery = useQuery({
    queryKey: ['ingest-events'],
    queryFn: () => api.listIngestEvents(200),
    staleTime: 5_000,
  })

  const events = eventsQuery.data?.events ?? []
  const filtered = React.useMemo(() => {
    const needle = q.trim().toLowerCase()
    let xs = events
    if (changedOnly) xs = xs.filter((e) => !!e.changed)
    if (!needle) return xs

    return xs.filter((e) => {
      const hay = `${e.doc_title} ${e.doc_source} ${e.doc_id} ${e.classification} ${e.retention} ${e.tags.join(' ')} ${e.embedding_backend} ${e.embeddings_model}`.toLowerCase()
      return hay.includes(needle)
    })
  }, [events, q, changedOnly])

  const columns = React.useMemo(
    () => [
      {
        header: 'Ingested',
        accessorKey: 'ingested_at',
        cell: (info: any) => <span className="text-xs">{formatUnixSeconds(Number(info.getValue() ?? 0))}</span>,
      },
      {
        header: 'Doc',
        accessorKey: 'doc_title',
        cell: (info: any) => {
          const e = info.row.original as IngestEventView
          return (
            <div className="space-y-1">
              <div className="font-medium">
                <Link to="/docs/$docId" params={{ docId: e.doc_id }} className="hover:underline">
                  {e.doc_title || e.doc_id}
                </Link>
              </div>
              <div className="text-xs text-muted-foreground">{e.doc_source}</div>
              <div className="flex flex-wrap gap-1">
                <Badge variant="outline">{e.classification}</Badge>
                <Badge variant="secondary">{e.retention}</Badge>
                {e.tags.slice(0, 3).map((t) => (
                  <Badge key={t} variant="secondary">
                    {t}
                  </Badge>
                ))}
                {e.tags.length > 3 ? <Badge variant="secondary">+{e.tags.length - 3}</Badge> : null}
              </div>
            </div>
          )
        },
      },
      {
        header: 'Changed',
        accessorKey: 'changed',
        cell: (info: any) => {
          const v = Boolean(info.getValue())
          const e = info.row.original as IngestEventView
          return (
            <div className="flex flex-wrap gap-1">
              {v ? <Badge variant="success">changed</Badge> : <Badge variant="outline">no</Badge>}
              {e.schema_drifted ? <Badge variant="warning">drift</Badge> : null}
            </div>
          )
        },
      },
      {
        header: 'Validation',
        accessorKey: 'validation_status',
        cell: (info: any) => {
          const status = String(info.getValue() ?? '').toLowerCase()
          if (!status) return <span className="text-xs text-muted-foreground">—</span>
          if (status === 'pass') return <Badge variant="success">pass</Badge>
          if (status === 'warn') return <Badge variant="warning">warn</Badge>
          if (status === 'fail') return <Badge variant="destructive">fail</Badge>
          return <Badge variant="outline">{status}</Badge>
        },
      },
      {
        header: 'Version',
        accessorKey: 'doc_version',
        cell: (info: any) => <span className="font-mono text-xs">v{String(info.getValue() ?? '')}</span>,
      },
      { header: 'Chunks', accessorKey: 'num_chunks' },
      {
        header: 'Embeddings',
        accessorKey: 'embeddings_model',
        cell: (info: any) => {
          const e = info.row.original as IngestEventView
          const model = e.embeddings_model || '—'
          return (
            <div className="text-xs">
              <div className="font-mono">{e.embedding_backend}</div>
              <div className="text-muted-foreground">{model}</div>
              <div className="text-muted-foreground">dim={e.embedding_dim}</div>
            </div>
          )
        },
      },
      {
        header: 'Notes',
        accessorKey: 'notes',
        cell: (info: any) => {
          const v = String(info.getValue() ?? '').trim()
          return v ? <span className="text-xs">{v}</span> : <span className="text-xs text-muted-foreground">—</span>
        },
      },
    ],
    [],
  )

  async function copyLatestRunJson() {
    if (!latestSyncRun || typeof navigator === 'undefined' || !navigator.clipboard) {
      setSyncCopyStatus('failed')
      return
    }

    try {
      await navigator.clipboard.writeText(JSON.stringify(latestSyncRun, null, 2))
      setSyncCopyStatus('copied')
      window.setTimeout(() => setSyncCopyStatus('idle'), 1500)
    } catch {
      setSyncCopyStatus('failed')
    }
  }

  function exportLatestRunJson() {
    if (!latestSyncRun || typeof window === 'undefined') return
    const payload = JSON.stringify(latestSyncRun, null, 2)
    const blob = new Blob([payload], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `gcs-sync-${latestSyncRun.run_id}.json`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const classifications = meta?.doc_classifications ?? ['public', 'internal', 'confidential', 'restricted']
  const retentions = meta?.doc_retentions ?? ['none', '30d', '90d', '1y', 'indefinite']
  const tabularSelected = Boolean(file && /\.(csv|tsv|xlsx|xlsm)$/i.test(file.name))

  return (
    <Page
      title="Ingest"
      description={
        uploadsEnabled
          ? 'Add documents to the index and review ingestion lineage.'
          : 'Ingestion controls are disabled for this deployment.'
      }
    >
      <Section
        title="Ingestion workspace"
        description="Add documents to the index and review the ingest lineage (audit feed)."
      >
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Upload file</CardTitle>
              <CardDescription>
                Supported: .md, .txt, .pdf, .csv, .tsv, .xlsx, .xlsm
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!uploadsEnabled ? (
                <div className="rounded-md border bg-muted p-3 text-sm">
                  Uploads are disabled for this deployment.
                  {meta?.public_demo_mode ? ' (Public read-only mode is enforced.)' : ''}
                </div>
              ) : null}

              <div className="space-y-2">
                <Label htmlFor="file">File</Label>
                <Input
                  id="file"
                  type="file"
                  accept=".md,.txt,.pdf,.csv,.tsv,.xlsx,.xlsm"
                  onChange={(e) => {
                    const next = e.target.files?.[0] ?? null
                    setFile(next)
                    if (!next || !/\.(csv|tsv|xlsx|xlsm)$/i.test(next.name)) {
                      setContractFile(null)
                    }
                  }}
                  disabled={!uploadsEnabled}
                />
                <div className="text-xs text-muted-foreground">
                  Max upload size: {meta?.max_upload_bytes ? `${meta.max_upload_bytes.toLocaleString()} bytes` : '—'}
                </div>
              </div>

              {tabularSelected ? (
                <div className="space-y-2">
                  <Label htmlFor="contractFile">Contract file (optional YAML)</Label>
                  <Input
                    id="contractFile"
                    type="file"
                    accept=".yaml,.yml"
                    onChange={(e) => setContractFile(e.target.files?.[0] ?? null)}
                    disabled={!uploadsEnabled}
                  />
                  <div className="text-xs text-muted-foreground">
                    Applies contract validation + schema drift tracking for tabular ingests.
                  </div>
                </div>
              ) : null}

              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="fileTitle">Title (optional)</Label>
                  <Input
                    id="fileTitle"
                    value={fileTitle}
                    onChange={(e) => setFileTitle(e.target.value)}
                    placeholder={file?.name ? file.name.replace(/\.[^.]+$/, '') : 'Defaults to file name'}
                    disabled={!uploadsEnabled}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="fileSource">Source</Label>
                  <Input
                    id="fileSource"
                    value={fileSource}
                    onChange={(e) => setFileSource(e.target.value)}
                    placeholder="e.g. ui:file"
                    disabled={!uploadsEnabled}
                  />
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="fileClassification">Classification</Label>
                  <Input
                    id="fileClassification"
                    value={fileClassification}
                    onChange={(e) => setFileClassification(e.target.value)}
                    list="classifications"
                    disabled={!uploadsEnabled}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="fileRetention">Retention</Label>
                  <Input
                    id="fileRetention"
                    value={fileRetention}
                    onChange={(e) => setFileRetention(e.target.value)}
                    list="retentions"
                    disabled={!uploadsEnabled}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="fileTags">Tags</Label>
                <Input
                  id="fileTags"
                  value={fileTags}
                  onChange={(e) => setFileTags(e.target.value)}
                  placeholder="comma,separated,tags"
                  disabled={!uploadsEnabled}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="fileNotes">Notes (optional)</Label>
                <Input
                  id="fileNotes"
                  value={fileNotes}
                  onChange={(e) => setFileNotes(e.target.value)}
                  placeholder="Why was this ingested?"
                  disabled={!uploadsEnabled}
                />
              </div>

              <div className="flex items-center gap-2">
                <Button
                  onClick={() => {
                    if (!file) return
                    uploadMutation.mutate({
                      file,
                      contractFile: contractFile ?? undefined,
                      title: fileTitle.trim() || undefined,
                      source: fileSource || undefined,
                      classification: fileClassification || undefined,
                      retention: fileRetention || undefined,
                      tags: fileTags.trim() || undefined,
                      notes: fileNotes || undefined,
                    })
                  }}
                  disabled={!uploadsEnabled || !file || uploadMutation.isPending}
                >
                  {uploadMutation.isPending ? 'Uploading…' : 'Ingest'}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setFile(null)
                    setContractFile(null)
                    setFileTitle('')
                    setFileTags('')
                    setFileNotes('')
                  }}
                  disabled={!uploadsEnabled}
                >
                  Reset
                </Button>
              </div>

              {uploadMutation.isError ? (
                <div className="rounded-md border bg-destructive/10 p-3 text-sm">
                  {(uploadMutation.error as Error).message}
                </div>
              ) : null}

              {uploadMutation.data ? (
                <div className="rounded-md border bg-muted p-3 text-sm">
                  Ingested{' '}
                  <Link to="/docs/$docId" params={{ docId: uploadMutation.data.doc_id }} className="underline">
                    {fileTitle.trim() || file?.name || uploadMutation.data.doc_id}
                  </Link>{' '}
                  (chunks: {uploadMutation.data.num_chunks}, changed:{' '}
                  {String(uploadMutation.data.changed)})
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Paste text</CardTitle>
              <CardDescription>Quickly add a note/runbook without uploading a file.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!uploadsEnabled ? (
                <div className="rounded-md border bg-muted p-3 text-sm">
                  Text ingestion is disabled for this deployment.
                  {meta?.public_demo_mode ? ' (Public read-only mode is enforced.)' : ''}
                </div>
              ) : null}

              <div className="space-y-2">
                <Label htmlFor="pasteTitle">Title</Label>
                <Input
                  id="pasteTitle"
                  value={pasteTitle}
                  onChange={(e) => setPasteTitle(e.target.value)}
                  placeholder="e.g. Incident Runbook"
                  disabled={!uploadsEnabled}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="pasteSource">Source</Label>
                <Input
                  id="pasteSource"
                  value={pasteSource}
                  onChange={(e) => setPasteSource(e.target.value)}
                  placeholder="e.g. ui:paste"
                  disabled={!uploadsEnabled}
                />
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="pasteClassification">Classification</Label>
                  <Input
                    id="pasteClassification"
                    value={pasteClassification}
                    onChange={(e) => setPasteClassification(e.target.value)}
                    list="classifications"
                    disabled={!uploadsEnabled}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="pasteRetention">Retention</Label>
                  <Input
                    id="pasteRetention"
                    value={pasteRetention}
                    onChange={(e) => setPasteRetention(e.target.value)}
                    list="retentions"
                    disabled={!uploadsEnabled}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="pasteTags">Tags</Label>
                <Input
                  id="pasteTags"
                  value={pasteTags}
                  onChange={(e) => setPasteTags(e.target.value)}
                  placeholder="comma,separated,tags"
                  disabled={!uploadsEnabled}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="pasteNotes">Notes (optional)</Label>
                <Input
                  id="pasteNotes"
                  value={pasteNotes}
                  onChange={(e) => setPasteNotes(e.target.value)}
                  placeholder="Why was this ingested?"
                  disabled={!uploadsEnabled}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="pasteText">Text</Label>
                <Textarea
                  id="pasteText"
                  value={pasteText}
                  onChange={(e) => setPasteText(e.target.value)}
                  rows={8}
                  placeholder="Paste text to index…"
                  disabled={!uploadsEnabled}
                />
              </div>

              <div className="flex items-center gap-2">
                <Button
                  onClick={() => {
                    if (!pasteTitle.trim() || !pasteText.trim()) return
                    pasteMutation.mutate({
                      title: pasteTitle.trim(),
                      source: pasteSource,
                      text: pasteText,
                      classification: pasteClassification || undefined,
                      retention: pasteRetention || undefined,
                      tags: parseTags(pasteTags),
                      notes: pasteNotes || undefined,
                    })
                  }}
                  disabled={!uploadsEnabled || !pasteTitle.trim() || !pasteText.trim() || pasteMutation.isPending}
                >
                  {pasteMutation.isPending ? 'Indexing…' : 'Ingest'}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setPasteTitle('')
                    setPasteTags('')
                    setPasteNotes('')
                    setPasteText('')
                  }}
                  disabled={!uploadsEnabled}
                >
                  Reset
                </Button>
              </div>

              {pasteMutation.isError ? (
                <div className="rounded-md border bg-destructive/10 p-3 text-sm">
                  {(pasteMutation.error as Error).message}
                </div>
              ) : null}

              {pasteMutation.data ? (
                <div className="rounded-md border bg-muted p-3 text-sm">
                  Ingested{' '}
                  <Link to="/docs/$docId" params={{ docId: pasteMutation.data.doc_id }} className="underline">
                    {pasteTitle.trim() || pasteMutation.data.doc_id}
                  </Link>{' '}
                  (chunks: {pasteMutation.data.num_chunks}, changed:{' '}
                  {String(pasteMutation.data.changed)})
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>

        <Card className="mt-4">
          <CardHeader>
            <CardTitle>GCS connector sync (admin)</CardTitle>
            <CardDescription>
              Run a one-off sync from Cloud Storage. Sync is add/update only and never deletes existing docs.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-md border bg-muted p-3 text-sm">{connectorAvailability.message}</div>

            {authMode !== 'none' ? (
              <div className="rounded-md border bg-muted p-3 text-xs text-muted-foreground">
                This action requires an admin principal when auth is enabled.
              </div>
            ) : null}

            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="gcsBucket">Bucket</Label>
                <Input
                  id="gcsBucket"
                  value={gcsBucket}
                  onChange={(e) => setGcsBucket(e.target.value)}
                  placeholder="my-bucket"
                  disabled={!connectorsEnabled}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="gcsPrefix">Prefix (optional)</Label>
                <Input
                  id="gcsPrefix"
                  value={gcsPrefix}
                  onChange={(e) => setGcsPrefix(e.target.value)}
                  placeholder="knowledge/"
                  disabled={!connectorsEnabled}
                />
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="gcsMaxObjects">Max objects (1-5000)</Label>
                <Input
                  id="gcsMaxObjects"
                  type="number"
                  min={1}
                  max={5000}
                  value={String(gcsMaxObjects)}
                  onChange={(e) => {
                    const parsed = Number.parseInt(e.target.value, 10)
                    if (!Number.isFinite(parsed)) {
                      setGcsMaxObjects(200)
                      return
                    }
                    setGcsMaxObjects(Math.max(1, Math.min(5000, parsed)))
                  }}
                  disabled={!connectorsEnabled}
                />
              </div>
              <div className="flex items-end gap-2 pb-2">
                <Checkbox
                  id="gcsDryRun"
                  checked={gcsDryRun}
                  onChange={(e) => setGcsDryRun(e.currentTarget.checked)}
                  disabled={!connectorsEnabled}
                />
                <Label htmlFor="gcsDryRun">Dry run (no writes)</Label>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="gcsClassification">Classification (optional)</Label>
                <Input
                  id="gcsClassification"
                  value={gcsClassification}
                  onChange={(e) => setGcsClassification(e.target.value)}
                  list="classifications"
                  disabled={!connectorsEnabled}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="gcsRetention">Retention (optional)</Label>
                <Input
                  id="gcsRetention"
                  value={gcsRetention}
                  onChange={(e) => setGcsRetention(e.target.value)}
                  list="retentions"
                  disabled={!connectorsEnabled}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="gcsTags">Tags (optional)</Label>
              <Input
                id="gcsTags"
                value={gcsTags}
                onChange={(e) => setGcsTags(e.target.value)}
                placeholder="comma,separated,tags"
                disabled={!connectorsEnabled}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="gcsNotes">Notes (optional)</Label>
              <Input
                id="gcsNotes"
                value={gcsNotes}
                onChange={(e) => setGcsNotes(e.target.value)}
                placeholder="Operator note for this run"
                disabled={!connectorsEnabled}
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button
                onClick={() =>
                  gcsSyncMutation.mutate({
                    bucket: gcsBucket.trim(),
                    prefix: gcsPrefix.trim() || undefined,
                    max_objects: Math.max(1, Math.min(5000, gcsMaxObjects)),
                    dry_run: gcsDryRun,
                    classification: gcsClassification.trim() || undefined,
                    retention: gcsRetention.trim() || undefined,
                    tags: parseTags(gcsTags),
                    notes: gcsNotes.trim() || undefined,
                  })
                }
                disabled={!connectorsEnabled || !gcsBucket.trim() || gcsSyncMutation.isPending}
              >
                {gcsSyncMutation.isPending ? 'Running sync…' : gcsDryRun ? 'Run dry sync' : 'Run sync'}
              </Button>

              <Button
                variant="outline"
                onClick={() => {
                  setGcsPrefix('')
                  setGcsMaxObjects(200)
                  setGcsDryRun(true)
                  setGcsClassification('internal')
                  setGcsRetention('none')
                  setGcsTags('')
                  setGcsNotes('')
                  setLatestSyncRun(null)
                  setSyncCopyStatus('idle')
                }}
                disabled={!connectorsEnabled || gcsSyncMutation.isPending}
              >
                Reset
              </Button>
            </div>

            {gcsSyncMutation.isError ? (
              <div className="rounded-md border bg-destructive/10 p-3 text-sm">
                {(gcsSyncMutation.error as Error).message}
              </div>
            ) : null}

            {latestSyncRun ? (
              <div className="space-y-3 rounded-md border bg-muted p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm">
                    <div className="font-medium">Last run: {latestSyncRun.run_id}</div>
                    <div className="text-xs text-muted-foreground">
                      {latestSyncRun.bucket}
                      {latestSyncRun.prefix ? ` / ${latestSyncRun.prefix}` : ''}
                      {' · '}
                      started {formatUnixSeconds(latestSyncRun.started_at)}
                      {' · '}
                      finished {formatUnixSeconds(latestSyncRun.finished_at)}
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button variant="outline" onClick={copyLatestRunJson}>
                      Copy JSON
                    </Button>
                    <Button variant="outline" onClick={exportLatestRunJson}>
                      Export JSON
                    </Button>
                  </div>
                </div>

                {syncCopyStatus === 'copied' ? (
                  <div className="text-xs text-muted-foreground">Copied run JSON to clipboard.</div>
                ) : null}
                {syncCopyStatus === 'failed' ? (
                  <div className="text-xs text-destructive">Copy failed. Use Export JSON instead.</div>
                ) : null}

                {gcsSummary ? (
                  <div className="flex flex-wrap gap-2 text-xs">
                    <Badge variant="outline">scanned: {gcsSummary.scanned}</Badge>
                    <Badge variant="outline">ingested: {gcsSummary.ingested}</Badge>
                    <Badge variant="outline">changed: {gcsSummary.changed}</Badge>
                    <Badge variant="outline">unchanged: {gcsSummary.unchanged}</Badge>
                    <Badge variant="outline">would_ingest: {gcsSummary.wouldIngest}</Badge>
                    <Badge variant="outline">skipped_unsupported: {gcsSummary.skippedUnsupported}</Badge>
                    <Badge variant="outline">dry_run: {String(latestSyncRun.dry_run)}</Badge>
                  </div>
                ) : null}

                {gcsSummary && gcsSummary.errors.length > 0 ? (
                  <div className="space-y-1">
                    <div className="text-sm font-medium">Errors</div>
                    <ul className="list-disc space-y-1 pl-5 text-xs">
                      {gcsSummary.errors.map((err) => (
                        <li key={err}>{err}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                <div className="space-y-2">
                  <div className="text-sm font-medium">Results ({latestSyncRun.results.length})</div>
                  <div className="max-h-64 overflow-auto rounded border">
                    <table className="min-w-full text-xs">
                      <thead className="bg-muted/60">
                        <tr className="text-left">
                          <th className="px-3 py-2">Object</th>
                          <th className="px-3 py-2">Status</th>
                          <th className="px-3 py-2">Doc</th>
                          <th className="px-3 py-2">Chunks</th>
                        </tr>
                      </thead>
                      <tbody>
                        {latestSyncRun.results.map((row) => {
                          const status = row.action === 'would_ingest' ? 'would_ingest' : row.changed ? 'changed' : 'unchanged'
                          return (
                            <tr key={`${row.gcs_uri}:${row.doc_id ?? row.action ?? row.content_sha256 ?? ''}`} className="border-t">
                              <td className="px-3 py-2 font-mono">{row.gcs_uri}</td>
                              <td className="px-3 py-2">{status}</td>
                              <td className="px-3 py-2">
                                {row.doc_id ? (
                                  <Link to="/docs/$docId" params={{ docId: row.doc_id }} className="underline">
                                    {row.doc_id}
                                  </Link>
                                ) : (
                                  '—'
                                )}
                              </td>
                              <td className="px-3 py-2">{row.num_chunks ?? '—'}</td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <datalist id="classifications">
          {classifications.map((c) => (
            <option key={c} value={c} />
          ))}
        </datalist>

        <datalist id="retentions">
          {retentions.map((r) => (
            <option key={r} value={r} />
          ))}
        </datalist>

        <Card className="mt-4">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Ingest events
              <Badge variant="secondary">{filtered.length}</Badge>
            </CardTitle>
            <CardDescription>
              Global lineage feed across documents. Use it to spot drift, investigate upgrades, and validate ingestion.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-col gap-2 md:flex-row md:items-center">
              <div className="flex-1">
                <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter by doc/source/tag/backend…" />
              </div>
              <div className="flex items-center gap-2">
                <Checkbox id="changedOnly" checked={changedOnly} onChange={(e) => setChangedOnly(e.currentTarget.checked)} />
                <Label htmlFor="changedOnly">Changed only</Label>
              </div>
            </div>

            {eventsQuery.isLoading ? <Spinner /> : null}
            {eventsQuery.isError ? (
              <div className="rounded-md border bg-destructive/10 p-3 text-sm">{(eventsQuery.error as Error).message}</div>
            ) : null}

            <DataTable<IngestEventView> data={filtered} columns={columns} height={560} />
          </CardContent>
        </Card>
      </Section>
    </Page>
  )
}
