"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import Link from "next/link";

type SectionId = "overview" | "layout" | "palette" | "shadows" | "typography";

interface NavGroup {
  label: string;
  items: { id: SectionId; label: string; icon: string }[];
}

const NAV: NavGroup[] = [
  {
    label: "Menu Principal",
    items: [{ id: "overview", label: "Visão Geral", icon: "◻" }],
  },
  {
    label: "Design Tokens",
    items: [
      { id: "layout", label: "Layout & Grid", icon: "▦" },
      { id: "palette", label: "Paleta Obsidian", icon: "◔" },
      { id: "shadows", label: "Sombras & Efeitos", icon: "✧" },
      { id: "typography", label: "Tipografia", icon: "T" },
    ],
  },
];

const OBSIDIAN_COLORS = [
  { name: "Tech Orange", hex: "#F97316", className: "from-brand-primary to-brand-primary-dark shadow-glow-orange" },
  { name: "Deep Blue", hex: "#3B82F6", className: "from-brand-secondary to-brand-secondary-dark shadow-glow-blue" },
  { name: "Deep Void", hex: "#050505", className: "from-obsidian-950 to-black border border-white/10" },
  { name: "Glass Surface", hex: "White Alpha 5%", className: "from-white/[0.06] to-white/[0.02] border border-white/10" },
];

export default function VSADesignShowcase() {
  const [activeSection, setActiveSection] = useState<SectionId>("layout");
  const [mobileOpen, setMobileOpen] = useState(false);
  const mainRef = useRef<HTMLDivElement>(null);

  const activeTitle = useMemo(() => {
    const item = NAV.flatMap((group) => group.items).find((entry) => entry.id === activeSection);
    return item?.label ?? "Design System";
  }, [activeSection]);

  const navigate = useCallback((id: SectionId) => {
    setActiveSection(id);
    setMobileOpen(false);
    mainRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  return (
    <div className="flex h-screen bg-obsidian-950 text-white overflow-hidden">
      <button
        type="button"
        onClick={() => setMobileOpen((prev) => !prev)}
        className="md:hidden fixed top-4 left-4 z-50 h-10 w-10 rounded-vsa-lg border border-white/10 bg-obsidian-800"
        aria-label="Menu"
      >
        ☰
      </button>

      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 z-30 bg-black/60"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside
        className={`
          fixed inset-y-0 left-0 z-40 w-[260px] border-r border-white/5 bg-obsidian-950/90 backdrop-blur-xl
          transition-transform duration-300 md:relative md:translate-x-0
          ${mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
        `}
      >
        <div className="h-full flex flex-col">
          <div className="px-7 py-6 border-b border-white/5">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-vsa-xl bg-vsa-brand shadow-glow-brand flex items-center justify-center font-bold">
                V
              </div>
              <div>
                <h1 className="text-[30px] leading-none font-bold">DeepCode</h1>
                <p className="text-sm text-brand-secondary font-semibold">VSA System v2.0</p>
              </div>
            </div>
          </div>

          <nav className="flex-1 px-4 py-6 space-y-8 overflow-y-auto">
            {NAV.map((group) => (
              <div key={group.label}>
                <p className="text-[11px] uppercase tracking-[0.2em] text-gray-600 mb-3 px-3">{group.label}</p>
                <div className="space-y-1">
                  {group.items.map((item) => {
                    const active = item.id === activeSection;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => navigate(item.id)}
                        className={`
                          relative w-full text-left rounded-vsa-lg px-3 py-2.5 text-sm transition-all flex items-center gap-3
                          ${
                            active
                              ? "bg-gradient-to-r from-brand-primary/20 to-transparent border-l-2 border-brand-primary text-white font-semibold"
                              : "text-gray-400 hover:text-white hover:bg-white/[0.03]"
                          }
                        `}
                      >
                        <span className={`text-xs ${active ? "text-brand-primary" : "text-gray-500"}`}>{item.icon}</span>
                        <span>{item.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </nav>

          <div className="p-4 border-t border-white/5">
            <div className="rounded-vsa-2xl border border-white/10 bg-white/[0.02] px-4 py-3">
              <p className="text-sm font-semibold">Status do Sistema</p>
              <p className="text-xs text-gray-400 mt-1 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-brand-primary animate-pulse" /> Online & Atualizado
              </p>
            </div>
          </div>
        </div>
      </aside>

      <main className="flex-1 flex flex-col overflow-hidden md:ml-0">
        <header className="h-[72px] border-b border-white/5 bg-obsidian-950/70 backdrop-blur-md px-6 md:px-8 flex items-center justify-between">
          <div className="ml-12 md:ml-0">
            <p className="text-sm font-semibold text-white">{activeTitle}</p>
            <p className="text-xs text-gray-500 tracking-[0.15em] uppercase">Diretrizes Técnicas</p>
          </div>

          <div className="flex items-center gap-3">
            <span className="rounded-full border border-white/10 bg-obsidian-800 px-3 py-1 text-xs text-gray-300 font-mono">main</span>
            <Link
              href="#"
              className="rounded-vsa-lg bg-vsa-brand px-4 py-2 text-sm font-semibold shadow-glow-brand hover:shadow-glow-orange-lg transition-all"
            >
              Exportar
            </Link>
          </div>
        </header>

        <div ref={mainRef} className="flex-1 overflow-y-auto px-6 md:px-8 py-8">
          {activeSection === "overview" && <OverviewSection />}
          {activeSection === "layout" && <LayoutSection />}
          {activeSection === "palette" && <PaletteSection />}
          {activeSection === "shadows" && <ShadowsSection />}
          {activeSection === "typography" && <TypographySection />}
        </div>
      </main>
    </div>
  );
}

function SectionHeader({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-8 border-l-2 border-brand-primary pl-5">
      <h2 className="text-5xl font-bold tracking-tight">{title}</h2>
      <p className="mt-2 text-2xl text-gray-400 max-w-5xl">{description}</p>
    </div>
  );
}

function OverviewSection() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Visão Geral Obsidian"
        description="Sistema visual dark-first com gradientes, glows coloridos e vidro fosco para uma experiência premium e legível."
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <article className="rounded-vsa-2xl bg-obsidian-900 border border-white/5 p-6 glass-panel">
          <h3 className="text-xl font-semibold mb-2">Brand Gradient</h3>
          <p className="text-gray-400 mb-4">Laranja Tech + Azul Deep com transição suave e luminosa.</p>
          <div className="h-24 rounded-vsa-xl bg-vsa-brand shadow-glow-brand" />
        </article>

        <article className="rounded-vsa-2xl bg-obsidian-900 border border-white/5 p-6 glass-panel">
          <h3 className="text-xl font-semibold mb-2">Sombras & Luz</h3>
          <p className="text-gray-400 mb-4">Substituímos sombras pretas por Colored Glows com aparência neon.</p>
          <div className="flex items-center gap-4">
            <div className="h-14 w-14 rounded-full bg-brand-primary/30 shadow-glow-orange" />
            <div className="h-14 w-14 rounded-full bg-brand-secondary/30 shadow-glow-blue" />
            <div className="h-14 w-14 rounded-full bg-vsa-brand shadow-glow-brand" />
          </div>
        </article>
      </div>
    </div>
  );
}

function LayoutSection() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="Grid & Estrutura"
        description="Um sistema de layout Glass-Shell que ocupa 100% da viewport, eliminando scrolls desnecessários."
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 rounded-vsa-2xl border border-white/5 bg-obsidian-900 p-6">
          <div className="rounded-vsa-2xl border border-white/10 bg-black/30 p-6 min-h-[360px] relative overflow-hidden">
            <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle,rgba(255,255,255,0.08)_1px,transparent_1px)] [background-size:14px_14px]" />
            <div className="relative h-full grid grid-cols-[220px_1fr] gap-4">
              <div className="rounded-vsa-xl bg-white/5 border border-white/10 p-4">
                <div className="h-8 w-8 rounded-full bg-white/15 mb-4" />
                <div className="h-2 rounded bg-white/10 mb-2" />
                <div className="h-2 w-2/3 rounded bg-white/10 mb-6" />
                <div className="mt-auto h-12 rounded-vsa-lg bg-brand-primary/30 border border-brand-primary/40" />
              </div>
              <div className="rounded-vsa-xl border border-white/10 bg-white/[0.02] p-4 flex items-center justify-center text-gray-500 font-mono">
                Fluid Content Area
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-vsa-2xl border border-brand-primary/70 bg-brand-primary/5 p-5">
            <h3 className="text-xl font-semibold">Sidebar Inteligente</h3>
            <p className="text-gray-400 mt-2">Comporta-se como drawer no mobile com backdrop blur para foco.</p>
          </div>
          <div className="rounded-vsa-2xl border border-brand-secondary/70 bg-brand-secondary/5 p-5">
            <h3 className="text-xl font-semibold">Container Fluido</h3>
            <p className="text-gray-400 mt-2">Área central limitada para evitar fadiga visual em ultrawide.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function PaletteSection() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="Cores da Marca (Gradual)"
        description="As cores Laranja Tech e Azul Deep são aplicadas através de gradientes e luzes, evitando blocos sólidos cansativos."
      />

      <div className="rounded-vsa-2xl border border-white/10 bg-vsa-brand shadow-glow-brand p-8 relative overflow-hidden">
        <p className="text-center text-5xl font-bold tracking-[0.1em]">BRAND GRADIENT</p>
        <span className="absolute bottom-4 right-4 rounded-vsa-md bg-brand-secondary/40 px-3 py-1 text-xs font-mono text-white/90">linear-gradient(135deg)</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {OBSIDIAN_COLORS.map((color) => (
          <div key={color.name} className={`rounded-vsa-2xl p-5 bg-gradient-to-b ${color.className} min-h-[170px]`}>
            <p className="text-2xl font-semibold mt-16">{color.name}</p>
            <p className="text-sm text-white/70 font-mono">{color.hex}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ShadowsSection() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="Sombras & Luz"
        description="Substituímos sombras pretas por Colored Glows que simulam emissão de luz neon."
      />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="rounded-vsa-2xl border border-white/10 bg-obsidian-900 p-8">
          <div className="flex flex-col items-center justify-center min-h-[280px] rounded-vsa-2xl bg-black/20 border border-white/5">
            <button
              type="button"
              className="rounded-vsa-xl bg-brand-primary px-10 py-5 text-xl font-bold text-white shadow-glow-orange-lg hover:shadow-glow-brand transition-all"
            >
              Botão Neon ⚡
            </button>
            <p className="mt-5 text-sm text-gray-500 font-mono">shadow-glow-brand</p>

            <div className="mt-8 flex items-center gap-5">
              <div className="h-14 w-14 rounded-full bg-brand-secondary shadow-glow-blue" />
              <div className="h-14 w-14 rounded-full bg-brand-primary shadow-glow-orange" />
              <div className="h-14 w-14 rounded-full bg-white/90 shadow-[0_0_20px_rgba(255,255,255,0.5)]" />
            </div>
          </div>
        </div>

        <div className="rounded-vsa-2xl border border-white/10 bg-gradient-to-br from-brand-primary/40 via-brand-secondary/30 to-purple-700/40 p-8 min-h-[280px] relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_0%_100%,rgba(249,115,22,0.5),transparent_45%),radial-gradient(circle_at_100%_0%,rgba(59,130,246,0.45),transparent_50%)]" />
          <div className="relative h-full flex items-center justify-center">
            <div className="glass-panel rounded-vsa-2xl border border-white/20 w-full max-w-[360px] px-8 py-10 text-center">
              <h3 className="text-4xl font-bold mb-3">Vidro Fosco</h3>
              <p className="text-lg text-gray-200">O efeito de vidro adiciona profundidade mantendo o contexto do fundo visível.</p>
              <div className="mt-6 h-1 w-20 mx-auto rounded-full bg-white/50" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TypographySection() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="Tipografia"
        description="Hierarquia clara com Inter para leitura máxima e JetBrains Mono para dados técnicos."
      />

      <div className="rounded-vsa-2xl border border-white/5 bg-obsidian-900 p-8 glass-panel">
        <div className="space-y-5">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">Display</p>
            <p className="text-6xl font-bold">Inter Semibold</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">Body</p>
            <p className="text-2xl text-gray-300">Texto corrido em alto contraste para contexto técnico e leitura prolongada.</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">Mono</p>
            <pre className="rounded-vsa-xl bg-black/30 border border-white/10 p-4 text-base text-gray-300 font-mono overflow-x-auto">
              <code>{`const design = { theme: "obsidian", glow: "colored", glass: true };`}</code>
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
