import { NAVIGATION_ITEMS, type PageId } from "../../app/routes";

function NavigationIcon({ page }: { page: PageId }) {
  const paths: Record<PageId, React.ReactNode> = {
    home: <><path d="M3 10.5 12 3l9 7.5" /><path d="M5.5 9.5V21h13V9.5" /></>,
    vectorization: <><path d="m4 18 5-5 4 4 3-3 4 4" /><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="8" cy="9" r="1.5" /></>,
    batch: <><rect x="4" y="4" width="12" height="12" rx="2" /><path d="M8 20h10a2 2 0 0 0 2-2V8" /></>,
    integrations: <><path d="M8 8h8v8H8z" /><path d="M3 12h5m8 0h5M12 3v5m0 8v5" /></>,
    tasks: <><path d="M7 4h10M7 9h10M7 14h7M7 19h5" /><path d="M3 4h.01M3 9h.01M3 14h.01M3 19h.01" /></>,
    license: <><path d="M12 3 5 6v5c0 4.6 2.8 8 7 10 4.2-2 7-5.4 7-10V6z" /><path d="m9 12 2 2 4-5" /></>,
    diagnostics: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.6v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" /></>,
  };
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      {paths[page]}
    </svg>
  );
}

interface NavigationProps {
  currentPage: PageId;
  onNavigate: (page: PageId) => void;
}

export function Navigation({ currentPage, onNavigate }: NavigationProps) {
  return (
    <nav className="side-navigation" aria-label="主要导航">
      {NAVIGATION_ITEMS.map((item) => (
        <button
          type="button"
          key={item.id}
          className={currentPage === item.id ? "is-active" : undefined}
          aria-current={currentPage === item.id ? "page" : undefined}
          onClick={() => onNavigate(item.id)}
        >
          <NavigationIcon page={item.id} />
          <span>{item.label}</span>
          {item.id === "batch" ? <span className="nav-lock">规划中</span> : null}
        </button>
      ))}
    </nav>
  );
}
