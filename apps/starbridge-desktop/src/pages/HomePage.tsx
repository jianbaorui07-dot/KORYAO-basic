import type { PageId } from "../app/routes";
import { EmptyState } from "../components/EmptyState/EmptyState";
import { TaskCard } from "../components/TaskCard/TaskCard";
import type { RuntimeStatus, VectorHistoryEvent } from "../types/api";

interface HomePageProps {
  status: RuntimeStatus;
  recentTasks: VectorHistoryEvent[];
  onNavigate: (page: PageId) => void;
}

export function HomePage({ status, recentTasks, onNavigate }: HomePageProps) {
  const ready = status.state === "connected";
  return (
    <div className="home-page">
      <section className="home-hero">
        <div>
          <span className="privacy-pill">仅本机处理</span>
          <h2>StarBridge 已准备好</h2>
          <p>在这台电脑上完成图片矢量化、批量任务和创意软件联动。<br />你的图片和设计文件不会上传到服务器。</p>
        </div>
        <div className="hero-trajectory" aria-hidden="true"><span /><span /><i>✦</i></div>
        <div className="hero-actions">
          <button type="button" className="primary" disabled={!ready} onClick={() => onNavigate("vectorization")}>开始图片矢量化</button>
          <button type="button" className="secondary" onClick={() => onNavigate("tasks")}>打开最近任务</button>
          <button type="button" className="quiet-button" onClick={() => onNavigate("integrations")}>查看软件联动</button>
        </div>
        {!ready ? <p className="inline-guidance">本地服务就绪后即可开始。你可以前往“设置与诊断”重新启动。</p> : null}
      </section>

      <section className="home-grid">
        <div className="section-panel recent-panel">
          <div className="section-heading"><div><span>最近任务</span><h3>继续上次的创作</h3></div><button type="button" className="text-button" onClick={() => onNavigate("tasks")}>查看全部</button></div>
          {recentTasks.length > 0 ? <TaskCard event={recentTasks[0]} compact /> : <EmptyState title="还没有任务记录" description="完成一次本机图片矢量化后，结果会出现在这里。" />}
        </div>
        <div className="section-panel software-panel">
          <div className="section-heading"><div><span>软件状态</span><h3>创意工具连接</h3></div></div>
          <ul className="software-list">
            <li><span className="software-monogram ai">Ai</span><div><strong>Illustrator</strong><small>公开交付协议可用，桌面联动待验收</small></div><span className="state-label planned">待验收</span></li>
            <li><span className="software-monogram ps">Ps</span><div><strong>Photoshop</strong><small>公开桥接实现已存在</small></div><span className="state-label neutral">需检测</span></li>
            <li><span className="software-monogram co">Co</span><div><strong>ComfyUI</strong><small>本机工作流按安装状态连接</small></div><span className="state-label neutral">需检测</span></li>
          </ul>
        </div>
      </section>
    </div>
  );
}
