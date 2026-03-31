"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavKey = "dashboard" | "my-reports" | "new-analysis" | "valuation" | "settings";

type SharedNavbarProps = {
  active?: NavKey;
};

const items: Array<{
  key: NavKey;
  label: string;
  href: string;
  icon: string;
}> = [
  { key: "dashboard", label: "Dashboard", href: "/client", icon: "dashboard" },
  { key: "my-reports", label: "My Reports", href: "/reports", icon: "description" },
  { key: "new-analysis", label: "New Analysis", href: "/analysis", icon: "analytics" },
  { key: "valuation", label: "Valuation", href: "/valuation", icon: "payments" },
  { key: "settings", label: "Settings", href: "/settings", icon: "settings" },
];

export default function SharedNavbar({ active }: SharedNavbarProps) {
  const pathname = usePathname();

  const resolvedActive: NavKey =
    active ||
    (pathname.startsWith("/report/") || pathname.startsWith("/reports")
      ? "my-reports"
      : pathname.startsWith("/analysis")
      ? "new-analysis"
      : pathname.startsWith("/valuation") || pathname.startsWith("/admin")
      ? "valuation"
      : pathname.startsWith("/settings")
      ? "settings"
      : "dashboard");

  return (
    <>
      <aside className="hidden md:flex flex-col fixed left-0 top-0 h-full p-4 space-y-2 bg-slate-50 w-64 z-40 text-sm font-semibold border-r border-slate-200/70">
        <div className="flex items-center gap-3 px-2 mb-8 mt-2">
          <div className="w-10 h-10 bg-blue-950 rounded-lg flex items-center justify-center text-white shadow-lg overflow-hidden">
            <span className="font-black">T</span>
          </div>
          <div>
            <h1 className="text-lg font-black text-blue-900 tracking-tight leading-none">Taqim Authority</h1>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest mt-1">Premium Real Estate</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1">
          {items.map((item) => {
            const selected = item.key === resolvedActive;
            return (
              <a
                key={item.key}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  selected
                    ? "bg-white text-blue-900 shadow-sm"
                    : "text-slate-500 hover:bg-blue-50 hover:text-blue-900"
                }`}
              >
                <span
                  className="material-symbols-outlined"
                  style={selected ? { fontVariationSettings: "'FILL' 1" } : undefined}
                >
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </a>
            );
          })}
        </nav>
      </aside>

      <nav className="md:hidden fixed bottom-0 left-0 w-full bg-white/95 backdrop-blur-md border-t border-slate-200 flex justify-around items-center h-16 px-2 z-50">
        {items.map((item) => {
          const selected = item.key === resolvedActive;
          return (
            <a key={item.key} className={`flex flex-col items-center gap-1 ${selected ? "text-blue-900" : "text-slate-400"}`} href={item.href}>
              <span
                className="material-symbols-outlined"
                style={selected ? { fontVariationSettings: "'FILL' 1" } : undefined}
              >
                {item.icon}
              </span>
              <span className="text-[10px] font-bold">{item.label.replace(" ", "")}</span>
            </a>
          );
        })}
      </nav>
    </>
  );
}
