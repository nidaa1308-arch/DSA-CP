import React from "react";
import {
  LayoutDashboard,
  UploadCloud,
  Map,
  BarChart3,
  FileText,
  Settings,
  Layers,
  AlertTriangle,
  Network,
  CheckSquare,
  FileCheck2,
} from "lucide-react";

export type Screen =
  | "landing"
  | "dashboard"
  | "new_investigation"
  | "upload"
  | "validation"
  | "crs_normalization"
  | "extract"
  | "sources"
  | "harmonize"
  | "conflict_dashboard"
  | "discrepancy"
  | "evidence"
  | "review"
  | "graph"
  | "reports"
  | "audit"
  | "settings";

interface SidebarProps {
  currentScreen: Screen;
  onSelectScreen: (screen: Screen) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentScreen, onSelectScreen }) => {
  // Simplified 6-item navigation matching the design specification
  const primaryNavItems: { id: Screen; label: string; icon: React.ReactNode; aliases: Screen[] }[] = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: <LayoutDashboard size={18} />,
      aliases: ["dashboard"],
    },
    {
      id: "upload",
      label: "Upload & Ingest",
      icon: <UploadCloud size={18} />,
      aliases: ["upload", "new_investigation", "validation", "crs_normalization"],
    },
    {
      id: "sources",
      label: "Multi-Source Viewer",
      icon: <Layers size={18} />,
      aliases: ["sources"],
    },
    {
      id: "discrepancy",
      label: "Discrepancy Map",
      icon: <Map size={18} />,
      aliases: ["discrepancy"],
    },
    {
      id: "conflict_dashboard",
      label: "Conflict Dashboard",
      icon: <AlertTriangle size={18} />,
      aliases: ["conflict_dashboard"],
    },
    {
      id: "evidence",
      label: "Spatial Evidence Card",
      icon: <FileCheck2 size={18} />,
      aliases: ["evidence"],
    },
    {
      id: "graph",
      label: "Spatial Evidence Graph",
      icon: <Network size={18} />,
      aliases: ["graph"],
    },
    {
      id: "review",
      label: "Review & Decision",
      icon: <CheckSquare size={18} />,
      aliases: ["review"],
    },
    {
      id: "reports",
      label: "Reports & Export",
      icon: <FileText size={18} />,
      aliases: ["reports", "audit"],
    },
    {
      id: "settings",
      label: "Settings",
      icon: <Settings size={18} />,
      aliases: ["settings"],
    },
  ];

  const isItemActive = (item: typeof primaryNavItems[0]) => {
    return item.id === currentScreen || item.aliases.includes(currentScreen);
  };

  return (
    <aside className="sidebar-image2">
      {/* Brand Header */}
      <div className="brand-header-image2" onClick={() => onSelectScreen("landing")}>
        <div className="gov-seal-image2">🏛️</div>
        <div className="brand-text-image2">
          <h2>BHUMI-FUSE</h2>
          <p>Harmonizing Land Records</p>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="nav-menu-image2">
        {primaryNavItems.map((item) => {
          const active = isItemActive(item);
          return (
            <button
              key={item.id}
              className={`nav-btn-image2 ${active ? "active" : ""}`}
              onClick={() => onSelectScreen(item.id)}
            >
              <span className="nav-icon-image2">{item.icon}</span>
              <span className="nav-label-image2">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Bottom Monument Watermark Artwork & SIH Tag */}
      <div className="sidebar-footer-image2">
        <svg
          className="monument-svg"
          viewBox="0 0 200 80"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Stylized Indian Heritage Monument Silhouette (India Gate / Fort Arch) */}
          <path
            d="M20 75V60H30V75H40V45H50V35H60V25H70V15H80V10H120V15H130V25H140V35H150V45H160V75H170V60H180V75H200V80H0V75H20Z"
            fill="currentColor"
            opacity="0.12"
          />
          <path
            d="M85 75V45C85 36.7 91.7 30 100 30C108.3 30 115 36.7 115 45V75H85Z"
            fill="currentColor"
            opacity="0.18"
          />
          <circle cx="100" cy="20" r="3" fill="currentColor" opacity="0.25" />
        </svg>
        <div className="sidebar-footer-text">
          <span>SIH 2026 • PS-26013</span>
        </div>
      </div>
    </aside>
  );
};
