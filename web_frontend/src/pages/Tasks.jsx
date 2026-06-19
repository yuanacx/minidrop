import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listTasks } from '../api'

const STATUS_CLASS = {
  PENDING: 'status-pending',
  RUNNING: 'status-running',
  DONE: 'status-done',
  FAILED: 'status-failed',
  UPLOADING: 'status-running',
}

export default function Tasks() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listTasks()
      .then((r) => setTasks(r.data || []))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="card center">
        <div className="spinner" />
        <p>加载任务列表…</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h2>任务列表</h2>
      <table>
        <thead>
          <tr><th>TID</th><th>状态</th><th>采集器</th><th>原因</th><th></th></tr>
        </thead>
        <tbody>
          {tasks.map((t) => (
            <tr key={t.tid}>
              <td><code>{t.tid}</code></td>
              <td><span className={`status-badge ${STATUS_CLASS[t.status] || ''}`}>{t.status}</span></td>
              <td>{t.collector}</td>
              <td className="muted">{t.status_reason}</td>
              <td><Link to={`/task/${t.tid}`}>详情</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
