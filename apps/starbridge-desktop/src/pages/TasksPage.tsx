import { EmptyState } from "../components/EmptyState/EmptyState";
import { TaskCard } from "../components/TaskCard/TaskCard";
import type { VectorHistoryEvent } from "../types/api";

export function TasksPage({ tasks, onStart }: { tasks: VectorHistoryEvent[]; onStart: () => void }) {
  return (
    <div className="standard-page">
      <header className="page-intro"><div><span className="page-kicker">本机任务记录</span><h2>查看已经真实完成的任务</h2><p>这里只记录脱敏摘要和质量指标，不记录原始图片路径，也不会同步到服务器。</p></div><button type="button" className="primary" onClick={onStart}>新建矢量化任务</button></header>
      {tasks.length > 0 ? <div className="task-list">{tasks.map((event) => <TaskCard event={event} key={event.eventId} />)}</div> : <EmptyState title="还没有任务记录" description="完成一次图片矢量化后，StarBridge 会在本机保存脱敏任务摘要。" action={<button type="button" className="secondary" onClick={onStart}>开始第一个任务</button>} />}
    </div>
  );
}
