import Link from "next/link";

export function AppLogo() {
  return (
    <Link className="app-logo" href="/" aria-label="work-support 대시보드로 이동">
      <span className="app-logo-mark" aria-hidden="true">
        <svg viewBox="0 0 40 40" role="img" focusable="false">
          <rect x="4" y="4" width="32" height="32" rx="10" />
          <path d="M12 14l4.2 12L20 17l3.8 9L28 14" />
          <path d="M12 29h16" />
        </svg>
      </span>
      <span className="app-logo-text">
        <strong>work-support</strong>
        <small>Dashboard</small>
      </span>
    </Link>
  );
}
