import { useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { artifactUrl, getTask, runAnalyze } from '../api'

const STATUS_CLASS = {
  PENDING: 'status-pending',
  RUNNING: 'status-running',
  DONE: 'status-done',
  FAILED: 'status-failed',
  UPLOADING: 'status-running',
}

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
    if (!tid || !analysisReady || tab === 'flame') return
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
    return <div className="card"><p className="error-text">URL 缺少 tid，请使用 /task/98b6424f 或 /task/result?tid=98b6424f</p></div>
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
          <p className="muted">TID: <code>{tid}</code></p>
          <p className="muted">创建: {formatTime(task?.created_at)}</p>
        </div>
        <div className="task-header-right">
          <span className={`status-badge ${STATUS_CLASS[task?.status] || ''}`}>{task?.status}</span>
          {task?.status === 'DONE' && !analysisReady && (
            <button type="button" onClick={onAnalyze}>生成火焰图</button>
          )}
        </div>
      </div>

      <p className="reason-line">{task?.status_reason}</p>

      <div className="tabs">
        {[
          ['flame', '火焰图'],
          ['topn', 'TopN 热点'],
          ['advice', '归因建议'],
        ].map(([k, label]) => (
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
            <p className="muted">请先完成火焰图分析</p>
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
            <p className="muted">请先完成火焰图分析</p>
          ) : topn === null ? (
            <div className="center"><div className="spinner" /></div>
          ) : (
            <ul className="advice-list">
              {topn.slice(0, 10).map((row, i) => (
                <li key={i}>
                  <strong>{row.function}</strong>
                  <span> — 热点占比靠前，建议结合源码与 perf 进一步定位（规则引擎见 analysis/rules.yaml）</span>
                </li>
              ))}
            </ul>
          )}
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
