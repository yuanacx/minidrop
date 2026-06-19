import { Link, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import Tasks from './pages/Tasks'
import TaskResult from './pages/TaskResult'

export default function App() {
  return (
    <>
      <nav>
        <strong>Mini-Drop</strong>
        <Link to="/">首页</Link>
        <Link to="/tasks">任务列表</Link>
      </nav>
      <div className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/task/:tid" element={<TaskResult />} />
          <Route path="/task/result" element={<TaskResult />} />
        </Routes>
      </div>
    </>
  )
}
