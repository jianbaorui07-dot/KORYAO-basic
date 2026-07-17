const INTEGRATIONS = [
  ["Ai", "Illustrator", "公开交付协议与测试存在；桌面端真实连接仍待单独验收。", "公开能力"],
  ["Ps", "Photoshop", "公开 UXP 与桥接实现存在；是否安装和连接需本机检测。", "需检测"],
  ["Co", "ComfyUI", "公开本机生命周期与计划接口存在；不会自动连接公网队列。", "本机优先"],
  ["Bl", "Blender", "公开桥接与场景证据实现存在；真实软件联动待验收。", "需检测"],
  ["CAD", "CAD / DXF", "公开 DXF 与 AutoCAD 相关实现存在；需要对应第三方软件。", "需第三方软件"],
];

export function IntegrationsPage() {
  return (
    <div className="standard-page">
      <header className="page-intro"><div><span className="page-kicker">软件联动</span><h2>连接你已经在使用的创意工具</h2><p>这里区分“公开代码已经存在”和“桌面端已经真实连接”。没有验收证据的连接不会显示为已就绪。</p></div><span className="local-badge">仅本机检测</span></header>
      <div className="integration-list">
        {INTEGRATIONS.map(([mark, name, description, state]) => <article key={name}><span className="integration-mark">{mark}</span><div><h3>{name}</h3><p>{description}</p></div><span className="state-label neutral">{state}</span></article>)}
      </div>
      <p className="truth-note">StarBridge 不会扫描未授权目录，也不会在后台启动公网服务。安装检测与真实连接将在有可审计证据后开放操作。</p>
    </div>
  );
}
