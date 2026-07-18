import symbolUrl from "../../assets/crenexus-software-icon.png";

interface BrandProps {
  compact?: boolean;
}

export function Brand({ compact = false }: BrandProps) {
  return (
    <div className={`brand-lockup${compact ? " brand-lockup-compact" : ""}`}>
      <img src={symbolUrl} alt="" aria-hidden="true" />
      <span>
        <strong>CreNexus</strong>
        {!compact ? <small>创枢 · AI 创意软件协同平台</small> : null}
      </span>
    </div>
  );
}
