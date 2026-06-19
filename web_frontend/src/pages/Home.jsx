import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createTask, getAgents } from '../api'

export default function Home() {
  const nav = useNavigate()
  const [agents, setAgents] = useState([])
  const [showModal, setShowModal] = useState(false)
  const [pid, setPid] = useState(1)
  const [duration, setDuration] = useState(10)
  const [hz, setHz] = useState(99)
  const [collector, setCollector] = useState('perf')
  const [targetIp, setTargetIp] = useState('127.0.0.1')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    getAgents(targetIp).then((r) => setAgents(r.data || [])).catch(() => setAgents([]))
  }, [targetIp])

  const submit = async () => {
    setSubmitting(true)
    try {
      const res = await createTask({
        target_ip: targetIp,
        pid: Number(pid),
        duration_sec: Number(duration),
        hz: Number(hz),
        collector,
      })
      setShowModal(false)
      nav(`/task/${res.data.tid}`)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <div className="hero card">
        <h1>Mini-Drop 性能采样</h1>
        <p className="muted">Agent 在线后即可对目标进程做 perf / py-spy / bpftrace 采集</p>
        <button type="button" className="primary" onClick={() => setShowModal(true)}>新建采样</button>
      </div>

      <div className="card">
        <h2>Agent 列表</h2>
        <table>
          <thead><tr><th>IP</th><th>状态</th><th>最后心跳</th></tr></thead>
          <tbody>
            {agents.length === 0 && (
              <tr><td colSpan={3} className="muted">暂无 Agent</td></tr>
            )}
            {agents.map((a, i) => (
              <tr key={i}>
                <td>{a.ip}</td>
                <td>
                  <span className={`dot ${a.online ? 'online' : 'offline'}`} />
                  {a.online ? '在线' : '离线'}
                </td>
                <td>{a.last_seen ? new Date(a.last_seen).toLocaleString('zh-CN') : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>新建采样</h3>
            <div className="form-grid">
              <label>目标 IP<input value={targetIp} onChange={(e) => setTargetIp(e.target.value)} /></label>
              <label>PID<input type="number" value={pid} onChange={(e) => setPid(e.target.value)} /></label>
              <label>时长 (s)<input type="number" value={duration} onChange={(e) => setDuration(e.target.value)} /></label>
              <label>Hz<input type="number" value={hz} onChange={(e) => setHz(e.target.value)} /></label>
              <label className="span-2">采集器
                <select value={collector} onChange={(e) => setCollector(e.target.value)}>
                  <option value="perf">perf（默认）</option>
                  <option value="pyspy">py-spy</option>
                  <option value="bpftrace">bpftrace</option>
                </select>
              </label>
            </div>
            <div className="modal-actions">
              <button type="button" className="ghost" onClick={() => setShowModal(false)}>取消</button>
              <button type="button" className="primary" disabled={submitting} onClick={submit}>
                {submitting ? '提交中…' : '开始采集'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
