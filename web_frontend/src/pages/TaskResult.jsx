import { useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import ReactECharts from 'echarts-for-react'
import {
  analyzeCP,
  artifactExists,
  artifactUrl,
  cpArtifactUrl,
  getTask,
  listCPSnapshots,
  runAnalyze,
} from '../api'

const STATUS_CLASS = {
  PENDING: 'status-pending',
  RUNNING: 'status-running',
  DONE: 'status-done',
  FAILED: 'status-failed',
  UPLOADING: 'status-running',
}

const TABS = [
  ['flame', '火焰图'],
  ['topn', 'TopN 热点'],
  ['advice', '归因建议'],
  ['pyspy', 'py-spy'],
  ['ebpf', 'eBPF'],
  ['cp', 'CP 回溯'],
]

function resolveTid(params, searchParams) {
  return params.tid || searchParams.get('tid') || ''
}

function formatTime(iso) {
  if (!iso) return '-'
  try {
    return new Date(iso).toLocaleString('zh-CN')
  } catch {
    return iso
  }
}

function normalizeBpfBuckets(data) {
  if (!data) return null
  if (Array.isArray(data.buckets) && data.buckets.length > 0) {
    return data.buckets.map((b) => ({
      label: b.label || b.name || String(b.bucket || '?'),
      count: b.count ?? b.value ?? 0,
    }))
  }
  return null
}

function BpftracePanel({ tid }) {
  const [loading, setLoading] = useState(true)
  const [buckets, setBuckets] = useState(null)
  const [note, setNote] = useState('')

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      for (const name of ['bpftrace.json', 'ebpf.json']) {
        try {
          const res = await fetch(artifactUrl(tid, name))
          if (!res.ok) continue
          const data = await res.json()
          const parsed = normalizeBpfBuckets(data)
          if (!cancelled && parsed) {
            setBuckets(parsed)
            setNote(data.note || '')
            setLoading(false)
            return
          }
        } catch {
          /* try next */
        }
      }
      if (!cancelled) {
        setBuckets(null)
        setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [tid])

  if (loading) {
    return <div className="center"><div className="spinner" /><p>加载 eBPF 数据…</p></div>
  }
  if (!buckets) {
    return <p className="muted empty-hint">本次采集未触发 eBPF 事件</p>
  }

  const option = {
    title: { text: 'IO 事件直方图', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: buckets.map((b) => b.label) },
    yAxis: { type: 'value', name: '次数' },
    series: [{ type: 'bar', data: buckets.map((b) => b.count), itemStyle: { color: '#0052d9' } }],
  }

  return (
    <>
      {note && <p className="muted">{note}</p>}
      <ReactECharts option={option} style={{ height: 420, width: '100%' }} />
    </>
  )
}

function PyspyPanel({ tid }) {
  const [state, setState] = useState('loading')
  const src = artifactUrl(tid, 'pyspy.svg')

  useEffect(() => {
    let cancelled = false
    artifactExists(src).then((ok) => {
      if (!cancelled) setState(ok ? 'ready' : 'missing')
    })
    return () => { cancelled = true }
  }, [src, tid])

  if (state === 'loading') {
    return <div className="center"><div className="spinner" /></div>
  }
  if (state === 'missing') {
    return <p className="muted empty-hint">py-spy 数据未采集</p>
  }
  return (
    <iframe
      title="py-spy flamegraph"
      src={src}
      style={{ width: '100%', height: 520, border: '1px solid var(--border)', borderRadius: 8 }}
    />
  )
}

function CPTimelinePanel() {
  const [snapshots, setSnapshots] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedTs, setSelectedTs] = useState(null)
  const [cpFlame, setCpFlame] = useState('')
  const [cpBusy, setCpBusy] = useState(false)
  const [cpErr, setCpErr] = useState('')

  useEffect(() => {
    listCPSnapshots(300)
      .then((res) => setSnapshots(res.data?.snapshots || []))
      .catch(() => setSnapshots([]))
      .finally(() => setLoading(false))
  }, [])

  const onSelect = async (ts) => {
    setSelectedTs(ts)
    setCpFlame('')
    setCpErr('')
    setCpBusy(true)
    try {
      await analyzeCP(ts)
      setCpFlame(cpArtifactUrl(ts, 'flamegraph.svg'))
    } catch (e) {
      setCpErr(e?.response?.data?.message || e.message || 'CP 分析失败')
    } finally {
      setCpBusy(false)
    }
  }

  if (loading) {
    return <div className="center"><div className="spinner" /><p>加载 CP 快照…</p></div>
  }
  if (snapshots.length === 0) {
    return <p className="muted empty-hint">最近 5 分钟内无 Continuous Profiling 快照（Agent 每 60s 上传 cp/）</p>
  }

  return (
    <div className="cp-panel">
      <p className="muted">最近 5 分钟 CP 快照（{snapshots.length} 个），点击时间点生成火焰图：</p>
      <div className="cp-timeline">
        {snapshots.map((s) => (
          <button
            key={s.ts}
            type="button"
            className={`cp-chip ${selectedTs === s.ts ? 'active' : ''}`}
            onClick={() => onSelect(s.ts)}
            disabled={cpBusy}
          >
            {formatTime(s.time)}
          </button>
        ))}
      </div>
      {cpBusy && <div className="center"><div className="spinner" /><p>生成 CP 火焰图…</p></div>}
      {cpErr && <p className="error-text">{cpErr}</p>}
      {cpFlame && !cpBusy && (
        <iframe
          title="cp-flamegraph"
          src={cpFlame}
          style={{ width: '100%', height: 520, border: '1px solid var(--border)', borderRadius: 8, marginTop: 12 }}
        />
      )}
    </div>
  )
}

export default function TaskResult() {
  const params = useParams()
  const [searchParams] = useSearchParams()
  const tid = resolveTid(params, searchParams)
  const [payload, setPayload] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('flame')
  const [topn, setTopn] = useState(null)
  const [artifactErr, setArtifactErr] = useState('')

  useEffect(() => {
    if (!tid) {
      setError('缺少任务 TID')
      setLoading(false)
      return undefined
    }
    let cancelled = false
    let timer

    const load = async () => {
      try {
        const res = await getTask(tid)
        if (cancelled) return
        setPayload(res)
        setError('')
      } catch (e) {
        if (!cancelled) setError(e?.response?.data?.message || e.message || '加载失败')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    timer = setInterval(load, 4000)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [tid])

  const task = payload?.data?.task
  const history = payload?.data?.history || []
  const analysisReady = task?.analysis_status === 'done'

  useEffect(() => {
    if (!tid || !analysisReady || tab === 'flame' || tab === 'cp') return
    if (tab !== 'topn' && tab !== 'advice') return
    fetch(artifactUrl(tid, 'top.json'))
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${r.status}`))))
      .then(setTopn)
      .catch(() => setTopn([]))
  }, [tid, analysisReady, tab])

  const flameSrc = useMemo(() => {
    if (!tid || !analysisReady) return ''
    return artifactUrl(tid, 'flamegraph.svg')
  }, [tid, analysisReady])

  const onAnalyze = async () => {
    setLoading(true)
    try {
      await runAnalyze(tid)
      const res = await getTask(tid)
      setPayload(res)
    } catch (e) {
      setError(e?.response?.data?.message || '分析失败')
    } finally {
      setLoading(false)
    }
  }

  if (!tid) {
    return <div className="card"><p className="error-text">URL 缺少 tid，请使用 /task/98b6424f</p></div>
  }

  if (loading && !payload) {
    return (
      <div className="card center">
        <div className="spinner" />
        <p>加载任务 {tid}…</p>
      </div>
    )
  }

  if (error && !task) {
    return (
      <div className="card">
        <p className="error-text">{error}</p>
        <Link to="/tasks">返回列表</Link>
      </div>
    )
  }

  return (
    <div className="card task-detail">
      <div className="task-header">
        <div>
          <h2>任务详情</h2>
          <p className="muted">TID: <code>{tid}</code> · 采集器: <code>{task?.collector || 'perf'}</code></p>
          <p className="muted">创建: {formatTime(task?.created_at)}</p>
        </div>
        <div className="task-header-right">
          <span className={`status-badge ${STATUS_CLASS[task?.status] || ''}`}>{task?.status}</span>
          {task?.status === 'DONE' && !analysisReady && task?.collector === 'perf' && (
            <button type="button" onClick={onAnalyze}>生成火焰图</button>
          )}
        </div>
      </div>

      <p className="reason-line">{task?.status_reason}</p>

      <div className="tabs">
        {TABS.map(([k, label]) => (
          <button key={k} type="button" className={tab === k ? 'active' : ''} onClick={() => setTab(k)}>
            {label}
          </button>
        ))}
      </div>

      {tab === 'flame' && (
        <div className="tab-panel">
          {!analysisReady && (
            <p className="muted">分析未完成，请点击「生成火焰图」或等待 analysis_status=done</p>
          )}
          {analysisReady && (
            <>
              {artifactErr && <p className="error-text">{artifactErr}</p>}
              <iframe
                title="flamegraph"
                src={flameSrc}
                onError={() => setArtifactErr('火焰图加载失败')}
                style={{ width: '100%', height: 520, border: '1px solid var(--border)', borderRadius: 8 }}
              />
            </>
          )}
        </div>
      )}

      {tab === 'topn' && (
        <div className="tab-panel">
          {!analysisReady ? (
            <p className="muted">请先完成 perf 火焰图分析</p>
          ) : topn === null ? (
            <div className="center"><div className="spinner" /><p>加载 TopN…</p></div>
          ) : (
            <table>
              <thead><tr><th>#</th><th>函数</th><th>样本数</th></tr></thead>
              <tbody>
                {topn.map((row, i) => (
                  <tr key={i}><td>{i + 1}</td><td><code>{row.function}</code></td><td>{row.samples}</td></tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === 'advice' && (
        <div className="tab-panel">
          {!analysisReady ? (
            <p className="muted">请先完成 perf 火焰图分析</p>
          ) : topn === null ? (
            <div className="center"><div className="spinner" /></div>
          ) : (
            <ul className="advice-list">
              {topn.slice(0, 10).map((row, i) => (
                <li key={i}>
                  <strong>{row.function}</strong>
                  <span> — 热点占比靠前，建议结合源码与 perf 进一步定位</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {tab === 'pyspy' && (
        <div className="tab-panel">
          {task?.status !== 'DONE' ? (
            <p className="muted">任务完成后查看 py-spy 产物</p>
          ) : (
            <PyspyPanel tid={tid} />
          )}
        </div>
      )}

      {tab === 'ebpf' && (
        <div className="tab-panel">
          {task?.status !== 'DONE' ? (
            <p className="muted">任务完成后查看 eBPF 产物</p>
          ) : (
            <BpftracePanel tid={tid} />
          )}
        </div>
      )}

      {tab === 'cp' && (
        <div className="tab-panel">
          <CPTimelinePanel />
        </div>
      )}

      <details className="history-block">
        <summary>状态迁移 ({history.length})</summary>
        <ul>
          {history.map((h, i) => (
            <li key={i}>
              {h.FromSt || h.from_st || '-'} → {h.ToSt || h.to_st} ({h.Reason || h.reason})
            </li>
          ))}
        </ul>
      </details>
    </div>
  )
}
