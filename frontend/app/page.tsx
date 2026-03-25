import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="bg-slate-50 text-slate-900 antialiased overflow-x-hidden">
      <nav className="fixed top-0 w-full flex justify-between items-center px-6 h-16 bg-white/80 backdrop-blur-md shadow-sm z-50">
        <div className="flex items-center gap-8">
          <span className="text-xl font-bold text-blue-950 tracking-tight">Taqim</span>
          <div className="hidden md:flex items-center gap-6">
            <a className="text-sm font-medium tracking-tight text-slate-500 hover:text-blue-800 transition-colors" href="#services">Services</a>
            <a className="text-sm font-medium tracking-tight text-slate-500 hover:text-blue-800 transition-colors" href="#pricing">Pricing</a>
            <a className="text-sm font-medium tracking-tight text-slate-500 hover:text-blue-800 transition-colors" href="#about">About</a>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Link className="text-sm font-medium tracking-tight text-slate-500 hover:text-blue-800 transition-colors" href="/login">Sign In</Link>
          <Link className="bg-gradient-to-br from-blue-950 to-blue-900 text-white px-5 py-2 rounded-lg text-sm font-semibold shadow-sm transition-all" href="/signup">
            Sign Up
          </Link>
        </div>
      </nav>

      <main className="relative pt-32 pb-20 overflow-hidden">
        <div className="absolute top-0 right-0 -translate-y-1/2 translate-x-1/4 w-[800px] h-[800px] bg-blue-200/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 left-0 translate-y-1/2 -translate-x-1/4 w-[600px] h-[600px] bg-amber-200/20 rounded-full blur-[100px]" />

        <div className="max-w-7xl mx-auto px-6 relative z-10">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100 border border-amber-200 mb-6">
                <span className="text-[11px] font-bold uppercase tracking-widest text-amber-900">Authority in Tunisian Real Estate</span>
              </div>

              <h1 className="text-5xl lg:text-7xl font-extrabold text-blue-950 leading-[1.1] tracking-tight mb-8">
                Know exactly what you are <span className="text-amber-600">buying</span> before you sign.
              </h1>
              <p className="text-lg lg:text-xl text-slate-600 leading-relaxed mb-10 max-w-xl">
                AI-powered property due diligence in Tunisia. Verify documents, assess risks,
                and get fair valuations with legal precision.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 items-center">
                <Link className="w-full sm:w-auto px-8 py-4 bg-amber-300 text-amber-900 font-bold rounded-xl shadow-lg transition-all text-center" href="/client">
                  Get your report
                </Link>
                <Link className="w-full sm:w-auto px-8 py-4 bg-transparent text-blue-950 font-bold hover:bg-slate-100 transition-colors rounded-xl text-center" href="/report/1">
                  View Sample Report
                </Link>
              </div>

              <div className="mt-16 flex flex-wrap gap-12 border-t border-slate-200 pt-10">
                <div className="flex flex-col">
                  <span className="text-3xl font-black text-blue-950">500+</span>
                  <span className="text-sm font-medium text-slate-500 uppercase tracking-wider">Reports Generated</span>
                </div>
                <div className="flex flex-col border-l border-slate-200 pl-12">
                  <span className="text-sm font-semibold text-blue-950 mb-2">Trusted by agencies across Tunisia</span>
                  <div className="flex gap-4 opacity-50 grayscale hover:grayscale-0 transition-all">
                    <span className="font-bold text-lg">RE/MAX</span>
                    <span className="font-bold text-lg">Tunisie Immo</span>
                    <span className="font-bold text-lg">Propriete.tn</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="relative lg:block">
              <div className="relative rounded-2xl bg-white shadow-[0px_32px_64px_rgba(15,45,94,0.12)] border border-slate-200 overflow-hidden">
                <div className="h-12 bg-slate-100 flex items-center px-4 gap-2 border-b border-slate-200">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-200" />
                    <div className="w-3 h-3 rounded-full bg-amber-200" />
                    <div className="w-3 h-3 rounded-full bg-blue-200" />
                  </div>
                  <div className="mx-auto bg-white px-6 py-1 rounded-md text-[10px] text-slate-500 font-medium">taqim.ai/dashboard/report-0482</div>
                </div>

                <div className="p-6 bg-white">
                  <div className="flex justify-between items-start mb-8">
                    <div>
                      <h3 className="text-xl font-bold text-blue-950 mb-1">Villa Jasmine, La Marsa</h3>
                      <p className="text-xs text-slate-500">Document ID: #TN-99-482-LM</p>
                    </div>
                    <div className="px-3 py-1 bg-blue-950 text-white rounded-full text-[10px] font-bold uppercase tracking-wider">Verified</div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <div className="bg-slate-100 p-4 rounded-xl">
                      <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Legal Status</p>
                      <div className="text-sm font-bold text-emerald-700">Titre (TF) Verified</div>
                    </div>
                    <div className="bg-slate-100 p-4 rounded-xl">
                      <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Market Valuation</p>
                      <div className="text-sm font-bold text-blue-950">850,000 TND</div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="h-2 w-3/4 bg-slate-200 rounded-full" />
                    <div className="h-2 w-full bg-slate-200 rounded-full" />
                    <div className="h-2 w-5/6 bg-slate-200 rounded-full" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <section id="services" className="py-24 bg-slate-100/50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-blue-950 mb-4">Complete Peace of Mind</h2>
            <p className="text-slate-600 max-w-2xl mx-auto">
              Our due diligence engine cross-references local data points to give you an objective verdict.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2 bg-white p-10 rounded-2xl shadow-sm border border-slate-200 flex flex-col justify-between">
              <div className="max-w-md">
                <h3 className="text-2xl font-bold text-blue-950 mb-4">Document Verification</h3>
                <p className="text-slate-600 leading-relaxed">
                  Instantly verify title deeds, building permits, and plans. AI flags discrepancies humans can miss.
                </p>
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-950 to-blue-900 p-10 rounded-2xl shadow-sm flex flex-col justify-between text-white">
              <div>
                <h3 className="text-2xl font-bold mb-4">Valuation Benchmarking</h3>
                <p className="text-blue-100/80 text-sm leading-relaxed">
                  Compare prices with hyper-local market data across Tunisia's coastal and urban hubs.
                </p>
              </div>
            </div>

            <div className="bg-white p-10 rounded-2xl shadow-sm border border-slate-200">
              <h3 className="text-2xl font-bold text-blue-950 mb-4">Risk Profiling</h3>
              <p className="text-slate-600 text-sm leading-relaxed">
                From legal constraints to environmental alerts, we flag what can impact investment outcomes.
              </p>
            </div>

            <div className="md:col-span-2 bg-white p-10 rounded-2xl shadow-sm border border-slate-200 flex items-center gap-10" id="about">
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-blue-950 mb-4">Legal Compliance</h3>
                <p className="text-slate-600 text-sm leading-relaxed mb-6">
                  Built with Tunisian legal expertise to keep every report aligned with current real estate regulation.
                </p>
                <ul className="space-y-2 text-xs font-bold text-blue-950">
                  <li>Updated 2024 legal framework</li>
                  <li>Registry consistency verification</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="w-full flex flex-col md:flex-row justify-between items-center px-12 py-12 gap-6 bg-slate-50 border-t border-slate-200" id="pricing">
        <div className="flex flex-col gap-2">
          <span className="font-bold text-blue-900 text-xl">Taqim</span>
          <span className="text-xs tracking-wider uppercase text-slate-400">© 2024 Taqim Real Estate Solutions. All rights reserved.</span>
        </div>
        <div className="flex flex-wrap justify-center gap-8 text-xs tracking-wider uppercase text-slate-400">
          <a className="hover:text-blue-700 transition-opacity" href="#">Privacy Policy</a>
          <a className="hover:text-blue-700 transition-opacity" href="#">Terms of Service</a>
          <a className="hover:text-blue-700 transition-opacity" href="#">Legal Notice</a>
          <a className="hover:text-blue-700 transition-opacity" href="#">Contact</a>
        </div>
      </footer>
    </div>
  );
}
