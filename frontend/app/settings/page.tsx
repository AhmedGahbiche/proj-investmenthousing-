"use client";

import SharedNavbar from "@/components/SharedNavbar";

export default function SettingsPage() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <SharedNavbar active="settings" />

      <section className="md:ml-64 max-w-5xl mx-auto px-6 py-10">
        <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm">
          <h1 className="text-3xl font-black text-blue-950 tracking-tight">Settings</h1>
          <p className="text-slate-600 mt-2">Account, notification, and workspace preferences will live here.</p>

          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="rounded-xl border border-slate-200 p-5">
              <p className="text-xs uppercase tracking-wider text-slate-500 font-bold">Profile</p>
              <p className="mt-2 text-sm text-slate-700">Manage your identity and contact information.</p>
            </div>
            <div className="rounded-xl border border-slate-200 p-5">
              <p className="text-xs uppercase tracking-wider text-slate-500 font-bold">Notifications</p>
              <p className="mt-2 text-sm text-slate-700">Set email and in-app alert preferences.</p>
            </div>
            <div className="rounded-xl border border-slate-200 p-5">
              <p className="text-xs uppercase tracking-wider text-slate-500 font-bold">Security</p>
              <p className="mt-2 text-sm text-slate-700">Control password and session behavior.</p>
            </div>
            <div className="rounded-xl border border-slate-200 p-5">
              <p className="text-xs uppercase tracking-wider text-slate-500 font-bold">Workspace</p>
              <p className="mt-2 text-sm text-slate-700">Configure default analysis and report options.</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
