"use client";

import { useState, useRef, useCallback } from "react";
import Link from "next/link";

/* ───────── types ───────── */
type SectionId =
  | "overview"
  | "palette"
  | "shadows"
  | "typography"
  | "layout";

interface NavGroup {
  label: string;
  items: { id: SectionId; label: string }[];
}

/* ───────── nav structure ───────── */
const NAV: NavGroup[] = [
  { label: "Menu Principal", items: [{ id: "overview", label: "Visão Geral" }] },
  {
    label: "Design Tokens",
    items: [
      { id: "layout", label: "Layout & Grid" },
      { id: "palette", label: "Paleta Obsidian" },
      { id: "shadows", label: "Sombras & Efeitos" },
      { id: "typography", label: "Tipografia" },
    ],
  },
];

/* ───────── obsidian scale data ───────── */
const OBSIDIAN_SCALE = [
  { name: "950", value: "#050505", tw: "bg-obsidian-950" },
  { name: "900", value: "#0A0A0A", tw: "bg-obsidian-900" },
  { name: "800", value: "#121212", tw: "bg-obsidian-800" },
  { name: "700", value: "#1A1A1A", tw: "bg-obsidian-700" },
  { name: "600", value: "#262626", tw: "bg-obsidian-600" },
  { name: "500", value: "#404040", tw: "bg-obsidian-500" },
];

/* ───────── type scale data ───────── */
const TYPE_SCALE = [
  { size: "text-5xl", px: "48px", weight: "font-bold", label: "Display" },
  { size: "text-4xl", px: "36px", weight: "font-bold", label: "H1" },
  { size: "text-3xl", px: "30px", weight: "font-semibold", label: "H2" },
  { size: "text-2xl", px: "24px", weight: "font-semibold", label: "H3" },
  { size: "text-xl", px: "20px", weight: "font-semibold", label: "H4" },
  { size: "text-lg", px: "18px", weight: "font-medium", label: "Large" },
  { size: "text-base", px: "16px", weight: "font-normal", label: "Body" },
  { size: "text-sm", px: "14px", weight: "font-normal", label: "Small" },
  { size: "text-xs", px: "12px", weight: "font-normal", label: "Caption" },
];

/* ───────── border radius tokens ───────── */
const RADII = [
  { name: "vsa-sm", value: "0.25rem", tw: "rounded-vsa-sm" },
  { name: "vsa-md", value: "0.375rem", tw: "rounded-vsa-md" },
  { name: "vsa-lg", value: "0.5rem", tw: "rounded-vsa-lg" },
  { name: "vsa-xl", value: "0.75rem", tw: "rounded-vsa-xl" },
  { name: "vsa-2xl", value: "1rem", tw: "rounded-vsa-2xl" },
  { name: "vsa-3xl", value: "1.5rem", tw: "rounded-vsa-3xl" },
];

/* ═══════════════════════════════════════════════════════════ */

export default function VSADesignShowcase() {
  const [activeSection, setActiveSection] = useState<SectionId>("layout");
  const [mobileOpen, setMobileOpen] = useState(false);
  const mainRef = useRef<HTMLDivElement>(null);

  const navigate = useCallback((id: SectionId) => {
    setActiveSection(id);
    setMobileOpen(false);
    // scroll to top of main area
    mainRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  return (
    <div className="flex h-screen bg-obsidian-950 text-white overflow-hidden">
      {/* ─── Mobile hamburger ─── */}
      <button
        type="button"
        onClick={() => setMobileOpen(!mobileOpen)}
        className="md:hidden fixed top-4 left-4 z-50 w-10 h-10 flex items-center justify-center rounded-vsa-lg bg-obsidian-800 border border-white/10 text-white"
        aria-label="Menu"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        >
          {mobileOpen ? (
            <>
              <line x1="4" y1="4" x2="16" y2="16" />
              <line x1="16" y1="4" x2="4" y2="16" />
            </>
          ) : (
            <>
              <line x1="3" y1="6" x2="17" y2="6" />
              <line x1="3" y1="10" x2="17" y2="10" />
              <line x1="3" y1="14" x2="17" y2="14" />
            </>
          )}
        </svg>
      </button>

      {/* ─── Mobile overlay ─── */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 z-30 bg-black/60"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* ─── Sidebar ─── */}
      <aside
        className={`
          w-72 flex-col border-r border-white/5 bg-obsidian-950/80 backdrop-blur-xl
          fixed inset-y-0 left-0 z-40 transition-transform duration-300
          md:relative md:translate-x-0 md:flex
          ${mobileOpen ? "translate-x-0 flex" : "-translate-x-full hidden md:flex"}
        `}
      >
        {/* Logo */}
        <div className="px-6 pt-6 pb-4 border-b border-white/5">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-vsa-xl bg-vsa-brand flex items-center justify-center text-white font-bold text-sm shadow-glow-brand">
              V
            </div>
            <div>
              <span className="text-sm font-semibold text-white group-hover:text-vsa-gradient transition-colors">
                DeepCode
              </span>
              <p className="text-[11px] text-gray-500 m-0">VSA System v2.0</p>
            </div>
          </Link>
        </div>

        {/* Nav groups */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {NAV.map((group) => (
            <div key={group.label}>
              <p className="text-[10px] uppercase tracking-widest text-gray-600 font-semibold px-3 mb-2">
                {group.label}
              </p>
              <div className="space-y-0.5">
                {group.items.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => navigate(item.id)}
                    className={`relative w-full text-left px-3 py-2 rounded-vsa-lg text-sm transition-all overflow-hidden ${
                      activeSection === item.id
                        ? "text-white font-semibold border-l-2 border-brand-primary bg-gradient-to-r from-brand-primary/20 to-transparent"
                        : "text-gray-400 hover:text-white hover:bg-white/[0.03]"
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-white/5">
          <div className="rounded-vsa-xl border border-white/10 bg-white/[0.02] p-3">
            <p className="text-xs font-semibold text-white mb-1">Status do Sistema</p>
            <div className="flex items-center gap-2 text-[11px] text-gray-400">
              <span className="w-2 h-2 rounded-full bg-brand-primary animate-pulse" />
              <span>Online & Atualizado</span>
            </div>
          </div>
        </div>
      </aside>

      {/* ─── Main area ─── */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="flex items-center justify-between px-6 md:px-8 py-4 border-b border-white/5 bg-obsidian-950/60 backdrop-blur-sm">
          <div className="flex items-center gap-3 ml-12 md:ml-0">
            <span className="text-xs px-3 py-1 rounded-full bg-obsidian-800 border border-white/10 text-gray-400 font-mono">
              main
            </span>
            <h1 className="text-sm font-medium text-white hidden sm:block">
              Design System
            </h1>
          </div>
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs px-4 py-2 rounded-vsa-lg bg-vsa-brand text-white font-medium shadow-glow-brand hover:shadow-glow-orange-lg transition-all"
          >
            Exportar
          </Link>
        </header>

        {/* Scrollable content */}
        <div
          ref={mainRef}
          className="flex-1 overflow-y-auto p-6 md:p-8 space-y-12"
        >
          {/* ════════ OVERVIEW ════════ */}
          {activeSection === "overview" && <SectionOverview />}

          {/* ════════ PALETTE ════════ */}
          {activeSection === "palette" && <SectionPalette />}

          {/* ════════ SHADOWS ════════ */}
          {activeSection === "shadows" && <SectionShadows />}

          {/* ════════ TYPOGRAPHY ════════ */}
          {activeSection === "typography" && <SectionTypography />}

          {/* ════════ LAYOUT ════════ */}
          {activeSection === "layout" && <SectionLayout />}
        </div>
      </main>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   Section components
   ═══════════════════════════════════════════════════════════ */

function SectionHeading({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-8">
      <h2 className="text-2xl font-bold text-vsa-gradient">{title}</h2>
      {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
}

/* ─── Overview ─── */
function SectionOverview() {
  const pillars = [
    {
      title: "Brand Gradient",
      desc: "Gradiente 135 deg de Laranja Tech para Azul Deep, aplicado em backgrounds, botões e textos.",
      demo: (
        <div className="h-20 rounded-vsa-2xl bg-vsa-brand shadow-glow-brand" />
      ),
    },
    {
      title: "Neon Button",
      desc: "Botões com sombra colorida que simula emissão de luz neon sobre a superfície escura.",
      demo: (
        <div className="flex items-center justify-center h-20">
          <button
            type="button"
            className="bg-brand-primary text-white px-6 py-3 rounded-vsa-xl font-medium shadow-glow-brand hover:shadow-glow-orange-lg transition-all"
          >
            Botão Neon
          </button>
        </div>
      ),
    },
    {
      title: "Colored Glows",
      desc: "Sombras coloridas substituem box-shadows pretas, criando profundidade luminosa.",
      demo: (
        <div className="flex items-center justify-center gap-4 h-20">
          <div className="w-12 h-12 rounded-full bg-brand-primary/20 shadow-glow-orange" />
          <div className="w-12 h-12 rounded-full bg-brand-secondary/20 shadow-glow-blue" />
          <div className="w-12 h-12 rounded-full bg-vsa-brand shadow-glow-brand" />
        </div>
      ),
    },
    {
      title: "Glassmorphism",
      desc: "Painéis de vidro fosco com backdrop-blur criam camadas de profundidade.",
      demo: (
        <div className="flex items-center justify-center h-20 bg-gradient-to-br from-brand-primary/10 via-transparent to-brand-secondary/10 rounded-vsa-xl">
          <div className="glass-panel rounded-vsa-xl px-6 py-3 text-sm text-gray-300">
            Glass Panel
          </div>
        </div>
      ),
    },
  ];

  return (
    <>
      <SectionHeading
        title="Visão Geral"
        subtitle="Os 4 pilares visuais do sistema de design Obsidian v2.0"
      />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {pillars.map((p) => (
          <div
            key={p.title}
            className="rounded-vsa-2xl bg-obsidian-900 border border-white/5 p-6 space-y-4"
          >
            <div>
              <h3 className="text-base font-semibold text-white">{p.title}</h3>
              <p className="text-sm text-gray-500 mt-1">{p.desc}</p>
            </div>
            {p.demo}
          </div>
        ))}
      </div>
    </>
  );
}

/* ─── Palette ─── */
function SectionPalette() {
  return (
    <>
      <SectionHeading
        title="Paleta Obsidian"
        subtitle="Cores da marca, escala escura e diretrizes de uso"
      />

      {/* Brand gradient banner */}
      <div className="bg-vsa-brand rounded-vsa-2xl p-8 mb-8">
        <p className="text-xs uppercase tracking-widest text-white/60 mb-2">
          Brand Gradient
        </p>
        <p className="text-2xl font-bold text-white mb-4">
          135deg — Orange to Blue
        </p>
        <div className="flex gap-4 text-xs text-white/70 font-mono">
          <span>#F97316</span>
          <span>&rarr;</span>
          <span>#EA580C</span>
          <span>&rarr;</span>
          <span>#3B82F6</span>
        </div>
      </div>

      {/* 4 color cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-brand-primary shadow-glow-orange rounded-vsa-2xl p-6">
          <p className="text-sm font-semibold text-white mb-1">Tech Orange</p>
          <p className="text-xs text-white/70 font-mono">#F97316</p>
          <p className="text-xs text-white/60 mt-2">brand-primary</p>
        </div>
        <div className="bg-brand-secondary shadow-glow-blue rounded-vsa-2xl p-6">
          <p className="text-sm font-semibold text-white mb-1">Deep Blue</p>
          <p className="text-xs text-white/70 font-mono">#3B82F6</p>
          <p className="text-xs text-white/60 mt-2">brand-secondary</p>
        </div>
        <div className="bg-obsidian-950 border border-white/10 rounded-vsa-2xl p-6">
          <p className="text-sm font-semibold text-white mb-1">Deep Void</p>
          <p className="text-xs text-white/70 font-mono">#050505</p>
          <p className="text-xs text-white/60 mt-2">obsidian-950</p>
        </div>
        <div className="glass-panel rounded-vsa-2xl p-6">
          <p className="text-sm font-semibold text-white mb-1">Glass Surface</p>
          <p className="text-xs text-white/70 font-mono">rgba(255,255,255,0.03)</p>
          <p className="text-xs text-white/60 mt-2">glass-panel</p>
        </div>
      </div>

      {/* Guideline */}
      <div className="rounded-vsa-xl bg-obsidian-900 border border-white/5 p-5 mb-8">
        <p className="text-sm text-gray-400 leading-relaxed">
          <span className="text-brand-primary font-medium">Diretriz:</span>{" "}
          As cores Laranja Tech e Azul Deep são aplicadas através de gradientes e luzes, evitando blocos sólidos cansativos. Superfícies devem permanecer na escala Obsidian.
        </p>
      </div>

      {/* Obsidian scale strip */}
      <div>
        <p className="text-xs uppercase tracking-widest text-gray-600 font-semibold mb-3">
          Obsidian Scale
        </p>
        <div className="flex gap-2">
          {OBSIDIAN_SCALE.map((s) => (
            <div key={s.name} className="text-center">
              <div
                className={`w-14 h-14 rounded-vsa-lg ${s.tw} border border-white/5`}
              />
              <p className="text-[10px] text-gray-500 mt-1.5 font-mono">
                {s.name}
              </p>
              <p className="text-[9px] text-gray-600 font-mono">{s.value}</p>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

/* ─── Shadows & Effects ─── */
function SectionShadows() {
  return (
    <>
      <SectionHeading
        title="Sombras & Efeitos"
        subtitle="Colored glows e botões neon sobre superfícies escuras"
      />

      {/* Neon button showcase */}
      <div className="rounded-vsa-2xl bg-obsidian-900 border border-white/5 p-8 mb-8">
        <p className="text-xs uppercase tracking-widest text-gray-600 font-semibold mb-6">
          Neon Button
        </p>
        <div className="flex flex-wrap gap-4 items-center">
          <button
            type="button"
            className="bg-brand-primary text-white px-6 py-3 rounded-vsa-xl font-medium shadow-glow-brand hover:shadow-glow-orange-lg transition-all"
          >
            Botão Neon
          </button>
          <button
            type="button"
            className="bg-brand-secondary text-white px-6 py-3 rounded-vsa-xl font-medium shadow-glow-blue hover:shadow-glow-blue-lg transition-all"
          >
            Botão Azul
          </button>
          <button
            type="button"
            className="bg-vsa-brand text-white px-6 py-3 rounded-vsa-xl font-medium shadow-glow-brand hover:shadow-glow-orange-lg transition-all"
          >
            Gradiente
          </button>
        </div>
      </div>

      {/* Glow swatches */}
      <div className="rounded-vsa-2xl bg-obsidian-900 border border-white/5 p-8 mb-8">
        <p className="text-xs uppercase tracking-widest text-gray-600 font-semibold mb-6">
          Colored Glows
        </p>
        <div className="flex flex-wrap gap-8 items-center">
          <div className="text-center">
            <div className="w-20 h-20 rounded-full bg-brand-primary/20 shadow-glow-orange mx-auto" />
            <p className="text-xs text-gray-500 mt-3 font-mono">glow-orange</p>
          </div>
          <div className="text-center">
            <div className="w-20 h-20 rounded-full bg-brand-secondary/20 shadow-glow-blue mx-auto" />
            <p className="text-xs text-gray-500 mt-3 font-mono">glow-blue</p>
          </div>
          <div className="text-center">
            <div className="w-20 h-20 rounded-full bg-vsa-brand shadow-glow-brand mx-auto" />
            <p className="text-xs text-gray-500 mt-3 font-mono">glow-brand</p>
          </div>
        </div>
      </div>

      {/* Large glows */}
      <div className="rounded-vsa-2xl bg-obsidian-900 border border-white/5 p-8 mb-8">
        <p className="text-xs uppercase tracking-widest text-gray-600 font-semibold mb-6">
          Large Glows (hover states)
        </p>
        <div className="flex flex-wrap gap-8 items-center">
          <div className="text-center">
            <div className="w-24 h-24 rounded-vsa-2xl bg-brand-primary/10 shadow-glow-orange-lg mx-auto" />
            <p className="text-xs text-gray-500 mt-3 font-mono">glow-orange-lg</p>
          </div>
          <div className="text-center">
            <div className="w-24 h-24 rounded-vsa-2xl bg-brand-secondary/10 shadow-glow-blue-lg mx-auto" />
            <p className="text-xs text-gray-500 mt-3 font-mono">glow-blue-lg</p>
          </div>
        </div>
      </div>

      {/* Glass panel shadow */}
      <div className="rounded-vsa-2xl bg-obsidian-900 border border-white/5 p-8 mb-8">
        <p className="text-xs uppercase tracking-widest text-gray-600 font-semibold mb-6">
          Glass Panel Shadow
        </p>
        <div className="flex items-center gap-8">
          <div className="w-32 h-32 rounded-vsa-2xl glass-panel shadow-glass-panel" />
          <div>
            <p className="text-xs text-gray-500 font-mono">shadow-glass-panel</p>
            <p className="text-xs text-gray-600 mt-1">
              0 8px 32px 0 rgba(0, 0, 0, 0.37)
            </p>
          </div>
        </div>
      </div>


      {/* Vidro Fosco integrado aos efeitos */}
      <div className="rounded-vsa-2xl bg-gradient-to-br from-brand-primary/10 via-transparent to-brand-secondary/10 border border-white/5 p-8 mb-8">
        <p className="text-xs uppercase tracking-widest text-gray-500 font-semibold mb-6">
          Vidro Fosco
        </p>
        <div className="glass-panel rounded-vsa-2xl p-6 max-w-lg">
          <h3 className="text-xl font-semibold text-white mb-2">Vidro Fosco</h3>
          <p className="text-sm text-gray-300 leading-relaxed mb-4">
            O efeito de vidro adiciona profundidade mantendo o contexto do fundo visível,
            usando blur, borda translúcida e brilho sutil.
          </p>
          <div className="h-1 w-24 rounded-full bg-vsa-brand shadow-glow-brand" />
        </div>
      </div>

      {/* Guideline */}
      <div className="rounded-vsa-xl bg-obsidian-900 border border-white/5 p-5">
        <p className="text-sm text-gray-400 leading-relaxed">
          <span className="text-brand-primary font-medium">Diretriz:</span>{" "}
          Substituímos sombras pretas por Colored Glows que simulam emissão de luz neon. Isso cria profundidade sem pesar o visual escuro.
        </p>
      </div>
    </>
  );
}

/* ─── Typography ─── */
function SectionTypography() {
  return (
    <>
      <SectionHeading
        title="Tipografia"
        subtitle="Famílias tipográficas e escala de tamanhos"
      />

      {/* Font families */}
      <div className="rounded-vsa-2xl bg-obsidian-900 border border-white/5 p-8 mb-8">
        <p className="text-xs uppercase tracking-widest text-gray-600 font-semibold mb-6">
          Font Families
        </p>
        <div className="space-y-6">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-gray-600 mb-2">
              Display / Títulos
            </p>
            <p className="text-3xl font-semibold text-white">
              Inter Semibold
            </p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-gray-600 mb-2">
              Body / Corpo
            </p>
            <p className="text-base text-gray-300">
              Inter Regular — A tipografia para texto corrido oferece legibilidade máxima em interfaces digitais sobre fundos escuros.
            </p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-gray-600 mb-2">
              Mono / Código
            </p>
            <div className="bg-obsidian-800 rounded-vsa-lg p-4">
              <pre className="font-mono text-sm text-gray-300">
                <code>{`const config = { theme: "obsidian", version: "2.0" };`}</code>
              </pre>
            </div>
          </div>
        </div>
      </div>

      {/* Type scale */}
      <div className="rounded-vsa-2xl bg-obsidian-900 border border-white/5 p-8">
        <p className="text-xs uppercase tracking-widest text-gray-600 font-semibold mb-6">
          Escala Tipográfica
        </p>
        <div className="space-y-4">
          {TYPE_SCALE.map((item) => (
            <div
              key={item.size}
              className="flex items-baseline gap-4 pb-4 border-b border-white/5 last:border-0 last:pb-0"
            >
              <span
                className={`flex-1 text-white ${item.size} ${item.weight} truncate`}
              >
                VSA Tecnologia
              </span>
              <span className="text-xs text-gray-600 w-12 text-right shrink-0">
                {item.px}
              </span>
              <code className="text-xs bg-obsidian-800 px-2 py-1 rounded-vsa-md text-gray-400 font-mono shrink-0">
                {item.size}
              </code>
              <span className="text-[10px] text-gray-600 w-14 shrink-0">
                {item.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

/* ─── Layout & Grid ─── */
function SectionLayout() {
  return (
    <>
      <SectionHeading
        title="Layout & Grid"
        subtitle="Grids responsivos, espaçamento e raios de borda"
      />

      {/* Grid demos */}
      <div className="space-y-6 mb-8">
        <div>
          <p className="text-xs uppercase tracking-widest text-gray-600 font-semibold mb-3">
            2 Colunas
          </p>
          <div className="grid grid-cols-2 gap-3">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="h-16 rounded-vsa-lg bg-obsidian-800 border border-white/5 flex items-center justify-center text-xs text-gray-500"
              >
                col {i}
              </div>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs uppercase tracking-widest text-gray-600 font-semibold mb-3">
            3 Colunas
          </p>
          <div className="grid grid-cols-3 gap-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-16 rounded-vsa-lg bg-obsidian-800 border border-white/5 flex items-center justify-center text-xs text-gray-500"
              >
                col {i}
              </div>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs uppercase tracking-widest text-gray-600 font-semibold mb-3">
            4 Colunas
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="h-16 rounded-vsa-lg bg-obsidian-800 border border-white/5 flex items-center justify-center text-xs text-gray-500"
              >
                col {i}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Spacing tokens */}
      <div className="rounded-vsa-2xl bg-obsidian-900 border border-white/5 p-8 mb-8">
        <p className="text-xs uppercase tracking-widest text-gray-600 font-semibold mb-4">
          Espaçamento
        </p>
        <div className="space-y-3">
          {[
            { name: "space-1", size: "0.25rem (4px)" },
            { name: "space-2", size: "0.5rem (8px)" },
            { name: "space-3", size: "0.75rem (12px)" },
            { name: "space-4", size: "1rem (16px)" },
            { name: "space-6", size: "1.5rem (24px)" },
            { name: "space-8", size: "2rem (32px)" },
          ].map((s) => (
            <div key={s.name} className="flex items-center gap-4">
              <div
                className="h-4 bg-brand-primary/30 rounded-sm"
                style={{ width: s.size.split(" ")[0] === "0.25rem" ? "4px" : s.size.split("(")[1]?.replace(")", "") }}
              />
              <code className="text-xs text-gray-400 font-mono w-20">
                {s.name}
              </code>
              <span className="text-xs text-gray-600">{s.size}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Border radius */}
      <div className="rounded-vsa-2xl bg-obsidian-900 border border-white/5 p-8">
        <p className="text-xs uppercase tracking-widest text-gray-600 font-semibold mb-4">
          Border Radius
        </p>
        <div className="flex flex-wrap gap-4">
          {RADII.map((r) => (
            <div key={r.name} className="text-center">
              <div
                className={`w-16 h-16 bg-obsidian-800 border border-white/10 ${r.tw}`}
              />
              <p className="text-[10px] text-gray-500 mt-2 font-mono">
                {r.name}
              </p>
              <p className="text-[9px] text-gray-600">{r.value}</p>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
