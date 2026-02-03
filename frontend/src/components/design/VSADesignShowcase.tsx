"use client";

import { useState } from "react";
import Link from "next/link";
import { Switch } from "@/components/ui/switch";

type TabId = "colors" | "typography" | "components" | "shadows";

type ColorShade = { name: string; hex: string; label?: string };

const colors: Record<string, ColorShade[]> = {
  orange: [
    { name: "50", hex: "#FFF7ED" },
    { name: "100", hex: "#FFEDD5" },
    { name: "200", hex: "#FED7AA" },
    { name: "300", hex: "#FDBA74" },
    { name: "400", hex: "#FB923C" },
    { name: "500", hex: "#F7941D", label: "Principal" },
    { name: "600", hex: "#E8611A", label: "Gradiente" },
    { name: "700", hex: "#C2410C" },
    { name: "800", hex: "#9A3412" },
    { name: "900", hex: "#7C2D12" },
  ],
  blue: [
    { name: "50", hex: "#EFF9FF" },
    { name: "100", hex: "#DEF1FF" },
    { name: "200", hex: "#B6E5FF" },
    { name: "300", hex: "#75D4FF" },
    { name: "400", hex: "#2CBFFF" },
    { name: "500", hex: "#00AEEF", label: "Principal" },
    { name: "600", hex: "#0077B5", label: "Gradiente" },
    { name: "700", hex: "#0369A1" },
    { name: "800", hex: "#075985" },
    { name: "900", hex: "#0C4A6E" },
  ],
  gray: [
    { name: "50", hex: "#FAFAFA" },
    { name: "100", hex: "#F4F4F5" },
    { name: "200", hex: "#E4E4E7" },
    { name: "300", hex: "#D4D4D8" },
    { name: "400", hex: "#A1A1AA" },
    { name: "500", hex: "#71717A" },
    { name: "600", hex: "#52525B" },
    { name: "700", hex: "#3F3F46" },
    { name: "800", hex: "#27272A" },
    { name: "900", hex: "#18181B" },
  ],
};

const tabs: { id: TabId; label: string }[] = [
  { id: "colors", label: "Cores" },
  { id: "typography", label: "Tipografia" },
  { id: "components", label: "Componentes" },
  { id: "shadows", label: "Sombras" },
];

const quickActions = [
  { icon: "🎫", title: "Tickets GLPI", subtitle: "Últimos chamados" },
  { icon: "⚠️", title: "Alertas Zabbix", subtitle: "Problemas ativos" },
  { icon: "📊", title: "Dashboard", subtitle: "Visão geral" },
  { icon: "📋", title: "Issues Linear", subtitle: "Tarefas do time" },
  { icon: "👤", title: "Novos s/ Atribuição", subtitle: "> 24h sem técnico" },
  { icon: "⏰", title: "Pendentes > 7 dias", subtitle: "Parados há muito tempo" },
];

const typeScale = [
  { size: "48px", name: "text-5xl", weight: "700" },
  { size: "36px", name: "text-4xl", weight: "700" },
  { size: "30px", name: "text-3xl", weight: "600" },
  { size: "24px", name: "text-2xl", weight: "600" },
  { size: "20px", name: "text-xl", weight: "600" },
  { size: "18px", name: "text-lg", weight: "500" },
  { size: "16px", name: "text-base", weight: "400" },
  { size: "14px", name: "text-sm", weight: "400" },
  { size: "12px", name: "text-xs", weight: "400" },
];

const shadowNeutral = [
  { name: "shadow-vsa-xs", shadow: "0 1px 2px rgba(24, 24, 27, 0.05)" },
  { name: "shadow-vsa-sm", shadow: "0 1px 3px rgba(24, 24, 27, 0.08), 0 1px 2px rgba(24, 24, 27, 0.04)" },
  { name: "shadow-vsa-md", shadow: "0 4px 6px rgba(24, 24, 27, 0.07), 0 2px 4px rgba(24, 24, 27, 0.05)" },
  { name: "shadow-vsa-lg", shadow: "0 10px 15px rgba(24, 24, 27, 0.08), 0 4px 6px rgba(24, 24, 27, 0.04)" },
  { name: "shadow-vsa-xl", shadow: "0 20px 25px rgba(24, 24, 27, 0.10), 0 8px 10px rgba(24, 24, 27, 0.04)" },
  { name: "shadow-vsa-2xl", shadow: "0 25px 50px rgba(24, 24, 27, 0.18)" },
];

const shadowColored = [
  { name: "shadow-vsa-orange", className: "shadow-vsa-orange", bgClass: "bg-vsa-orange" },
  { name: "shadow-vsa-orange-lg", className: "shadow-vsa-orange-lg", bgClass: "bg-vsa-orange" },
  { name: "shadow-vsa-blue", className: "shadow-vsa-blue", bgClass: "bg-vsa-blue" },
  { name: "shadow-vsa-blue-lg", className: "shadow-vsa-blue-lg", bgClass: "bg-vsa-blue" },
  { name: "shadow-vsa-brand", className: "shadow-vsa-brand", bgClass: "bg-vsa-brand" },
];

export default function VSADesignShowcase() {
  const [activeTab, setActiveTab] = useState<TabId>("colors");
  const [switchDemoOn, setSwitchDemoOn] = useState(true);

  return (
    <div className="min-h-screen bg-vsa-soft font-body">
      <header className="bg-white border-b border-vsa-gray-300 py-4 px-8 flex items-center justify-between shadow-vsa-sm">
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="w-12 h-12 rounded-vsa-xl bg-vsa-brand flex items-center justify-center text-white font-bold text-xl shadow-vsa-brand hover:shadow-vsa-orange transition-all"
            title="Voltar ao Chat"
            aria-label="Voltar ao Chat"
          >
            V
          </Link>
          <div>
            <h1 className="text-xl font-bold text-vsa-gradient m-0">VSA Design System</h1>
            <p className="text-[13px] text-vsa-gray-500 m-0">Soluções em Tecnologia</p>
          </div>
          <Link
            href="/"
            className="vsa-btn vsa-btn-outline text-sm py-2 px-4 rounded-lg"
          >
            Voltar ao Chat
          </Link>
        </div>
        <div className="vsa-status vsa-status-online py-2 px-4 bg-vsa-success-light rounded-full text-[13px] text-vsa-success-dark font-medium">
          <span className="vsa-status-dot" />
          <span>VSA ATIVO</span>
        </div>
      </header>

      <nav className="bg-white border-b border-vsa-gray-300 px-8 flex gap-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`py-4 px-6 border-b-2 text-sm font-normal transition-all duration-200 ${
              activeTab === tab.id
                ? "border-vsa-orange-500 text-vsa-orange-500 font-semibold"
                : "border-transparent text-vsa-gray-500"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="vsa-main-background min-h-[60vh] p-8 max-w-[1400px] mx-auto">
        {activeTab === "colors" && (
          <div>
            <h2 className="text-2xl font-semibold text-vsa-gray-900 mb-6">Paleta de Cores</h2>

            <section className="mb-12">
              <h3 className="text-base font-semibold text-vsa-gray-700 mb-4">Gradientes da Marca</h3>
              <div className="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
                <div className="h-[120px] bg-vsa-brand rounded-vsa-2xl flex items-end p-4 text-white font-semibold shadow-vsa-brand">
                  Gradiente Principal (135°)
                </div>
                <div className="h-[120px] bg-vsa-orange rounded-vsa-2xl flex items-end p-4 text-white font-semibold shadow-vsa-orange">
                  Gradiente Laranja
                </div>
                <div className="h-[120px] bg-vsa-blue rounded-vsa-2xl flex items-end p-4 text-white font-semibold shadow-vsa-blue">
                  Gradiente Azul
                </div>
              </div>
            </section>

            {Object.entries(colors).map(([colorName, shades]) => (
              <section key={colorName} className="mb-8">
                <h3 className="text-base font-semibold text-vsa-gray-700 mb-4">
                  {colorName === "orange" ? "Laranja VSA" : colorName === "blue" ? "Azul VSA" : "Neutros"}
                </h3>
                <div className="flex gap-2 flex-wrap">
                  {shades.map((shade) => (
                    <div key={shade.name} className="text-center">
                        <div
                          className={`w-20 h-20 rounded-vsa-xl shadow-vsa-sm mb-2 ${
                            shade.name === "50" || shade.name === "100" ? "border border-vsa-gray-400" : "border-0"
                          }`}
                          style={{ backgroundColor: shade.hex }}
                        />
                      <p className="text-xs font-semibold text-vsa-gray-700 m-0">{shade.name}</p>
                      <p className="text-[11px] text-vsa-gray-500 m-0 mt-0.5">{shade.hex}</p>
                      {shade.label && (
                        <span
                          className={`text-[9px] px-1.5 py-0.5 rounded mt-1 inline-block ${
                            colorName === "orange" ? "bg-vsa-orange-50 text-vsa-orange-600" : "bg-vsa-blue-50 text-vsa-blue-600"
                          }`}
                        >
                          {shade.label}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            ))}

            <section>
              <h3 className="text-base font-semibold text-vsa-gray-700 mb-4">Cores Semânticas</h3>
              <div className="flex gap-4 flex-wrap">
                {[
                  { name: "Sucesso", bg: "bg-vsa-success", light: "bg-vsa-success-light" },
                  { name: "Erro", bg: "bg-vsa-error", light: "bg-vsa-error-light" },
                  { name: "Aviso", bg: "bg-vsa-orange-500", light: "bg-vsa-orange-100" },
                  { name: "Info", bg: "bg-vsa-blue-500", light: "bg-vsa-blue-100" },
                ].map((item) => (
                  <div key={item.name} className="flex flex-col gap-1 items-center">
                    <div className="flex gap-1">
                      <div className={`w-12 h-12 rounded-vsa-lg ${item.light}`} />
                      <div className={`w-12 h-12 rounded-vsa-lg ${item.bg}`} />
                    </div>
                    <span className="text-xs text-vsa-gray-600">{item.name}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}

        {activeTab === "typography" && (
          <div>
            <h2 className="text-2xl font-semibold text-vsa-gray-900 mb-6">Tipografia</h2>

            <section className="bg-white rounded-vsa-2xl p-8 shadow-vsa-sm mb-6">
              <h3 className="text-sm font-semibold text-vsa-gray-500 mb-6 uppercase tracking-wider">
                Font Families Recomendadas
              </h3>
              <div className="grid gap-6">
                <div>
                  <p className="text-xs text-vsa-gray-400 mb-2">Display / Títulos</p>
                  <p className="font-display text-3xl font-semibold text-vsa-gray-900 m-0">Poppins Semibold</p>
                </div>
                <div>
                  <p className="text-xs text-vsa-gray-400 mb-2">Body / Corpo</p>
                  <p className="font-body text-base font-normal text-vsa-gray-700 m-0">
                    Inter Regular - A tipografia para texto corrido oferece legibilidade máxima em interfaces digitais.
                  </p>
                </div>
                <div>
                  <p className="text-xs text-vsa-gray-400 mb-2">Mono / Código</p>
                  <p className="font-mono text-sm text-vsa-gray-600 m-0 bg-vsa-gray-100 p-3 rounded-vsa-lg">
                    JetBrains Mono - const vsaConfig = {"{...}"};
                  </p>
                </div>
              </div>
            </section>

            <section className="bg-white rounded-vsa-2xl p-8 shadow-vsa-sm">
              <h3 className="text-sm font-semibold text-vsa-gray-500 mb-6 uppercase tracking-wider">
                Escala Tipográfica
              </h3>
              <div className="grid gap-4">
                {typeScale.map((item) => (
                  <div
                    key={item.name}
                    className="flex items-baseline gap-6 pb-4 border-b border-vsa-gray-300"
                  >
                    <span
                      className="flex-1 text-vsa-gray-900"
                      style={{ fontSize: item.size, fontWeight: item.weight }}
                    >
                      VSA Tecnologia
                    </span>
                    <span className="text-xs text-vsa-gray-400 w-20">{item.size}</span>
                    <code className="text-xs bg-vsa-gray-100 px-2 py-1 rounded text-vsa-gray-600 w-[100px]">
                      {item.name}
                    </code>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}

        {activeTab === "components" && (
          <div>
            <h2 className="text-2xl font-semibold text-vsa-gray-900 mb-6">Componentes</h2>

            <section className="bg-white rounded-vsa-2xl p-8 shadow-vsa-sm mb-6">
              <h3 className="text-sm font-semibold text-vsa-gray-500 mb-6 uppercase tracking-wider">Botões</h3>
              <div className="flex gap-4 flex-wrap items-center">
                <button type="button" className="vsa-btn vsa-btn-primary">
                  Primary
                </button>
                <button type="button" className="vsa-btn vsa-btn-orange">
                  Orange
                </button>
                <button type="button" className="vsa-btn vsa-btn-blue">
                  Blue
                </button>
                <button type="button" className="vsa-btn vsa-btn-outline">
                  Outline
                </button>
                <button type="button" className="vsa-btn vsa-btn-ghost">
                  Ghost
                </button>
              </div>
            </section>

            <section className="bg-white rounded-vsa-2xl p-8 shadow-vsa-sm mb-6">
              <h3 className="text-sm font-semibold text-vsa-gray-500 mb-6 uppercase tracking-wider">
                Quick Action Cards (Nexus AI Style)
              </h3>
              <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">
                {quickActions.map((item, i) => (
                  <div key={i} className="vsa-quick-action">
                    <div className="vsa-quick-action-icon">{item.icon}</div>
                    <div className="vsa-quick-action-content">
                      <p className="vsa-quick-action-title m-0">{item.title}</p>
                      <p className="vsa-quick-action-subtitle m-0">{item.subtitle}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="bg-white rounded-vsa-2xl p-8 shadow-vsa-sm mb-6">
              <h3 className="text-sm font-semibold text-vsa-gray-500 mb-6 uppercase tracking-wider">Cards</h3>
              <div className="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4">
                <div className="vsa-card">
                  <p className="font-semibold text-vsa-gray-900 m-0 mb-2">Card padrão</p>
                  <p className="text-sm text-vsa-gray-600 m-0">Borda neutra, hover suave.</p>
                </div>
                <div className="vsa-card-gradient">
                  <p className="font-semibold text-vsa-gray-900 m-0 mb-2">Card com borda gradiente</p>
                  <p className="text-sm text-vsa-gray-600 m-0">Hover revela borda laranja/azul.</p>
                </div>
                <div className="vsa-card-active">
                  <p className="font-semibold text-vsa-gray-900 m-0 mb-2">Card ativo</p>
                  <p className="text-sm text-vsa-gray-600 m-0">Seleção / destaque.</p>
                </div>
              </div>
            </section>

            <section className="bg-white rounded-vsa-2xl p-8 shadow-vsa-sm mb-6">
              <h3 className="text-sm font-semibold text-vsa-gray-500 mb-6 uppercase tracking-wider">Sessões (Sidebar)</h3>
              <div className="flex gap-4 flex-wrap">
                <div className="vsa-session">
                  <p className="vsa-session-title m-0">Sessão inativa</p>
                  <p className="vsa-session-subtitle m-0">Última atividade há 2h</p>
                </div>
                <div className="vsa-session vsa-session-active">
                  <p className="vsa-session-title m-0">Sessão ativa</p>
                  <p className="vsa-session-subtitle m-0">Agora</p>
                </div>
                <div className="vsa-session">
                  <span className="vsa-session-badge">3</span>
                  <p className="vsa-session-title m-0">Sessão com badge</p>
                  <p className="vsa-session-subtitle m-0">3 mensagens</p>
                </div>
              </div>
            </section>

            <section className="bg-white rounded-vsa-2xl p-8 shadow-vsa-sm mb-6">
              <h3 className="text-sm font-semibold text-vsa-gray-500 mb-6 uppercase tracking-wider">Switch (Toggle)</h3>
              <div className="flex flex-wrap gap-6 items-center">
                <Switch checked={!switchDemoOn} label="Desligado" onClick={() => setSwitchDemoOn(true)} />
                <Switch checked={switchDemoOn} label="Ligado (laranja VSA)" onClick={() => setSwitchDemoOn(!switchDemoOn)} />
              </div>
              <p className="text-xs text-vsa-gray-500 mt-4 m-0">
                Quando ligado: borda e fundo laranja VSA (#F7941D), sombra laranja.
              </p>
            </section>

            <section className="bg-white rounded-vsa-2xl p-8 shadow-vsa-sm mb-6">
              <h3 className="text-sm font-semibold text-vsa-gray-500 mb-6 uppercase tracking-wider">Badges</h3>
              <div className="flex gap-3 flex-wrap">
                <span className="vsa-badge vsa-badge-orange">Laranja</span>
                <span className="vsa-badge vsa-badge-blue">Azul</span>
                <span className="vsa-badge vsa-badge-success">Sucesso</span>
                <span className="vsa-badge vsa-badge-error">Erro</span>
                <span className="vsa-badge vsa-badge-gray">Neutro</span>
                <span className="vsa-badge vsa-badge-gradient">Gradiente</span>
              </div>
            </section>

            <section className="bg-white rounded-vsa-2xl p-8 shadow-vsa-sm">
              <h3 className="text-sm font-semibold text-vsa-gray-500 mb-6 uppercase tracking-wider">Inputs</h3>
              <div className="grid gap-4 max-w-[400px]">
                <input type="text" placeholder="Digite sua mensagem ou use o microfone..." className="vsa-input" />
                <input type="text" placeholder="Input com foco laranja (clique)" className="vsa-input focus:border-vsa-orange-500 focus:ring-2 focus:ring-vsa-orange/20" />
                <input type="text" placeholder="Input com erro" className="vsa-input vsa-input-error" />
              </div>
            </section>
          </div>
        )}

        {activeTab === "shadows" && (
          <div>
            <h2 className="text-2xl font-semibold text-vsa-gray-900 mb-6">Sombras</h2>

            <section className="bg-white rounded-vsa-2xl p-8 shadow-vsa-sm mb-6">
              <h3 className="text-sm font-semibold text-vsa-gray-500 mb-6 uppercase tracking-wider">
                Sombras Neutras
              </h3>
              <div className="flex gap-6 flex-wrap">
                {shadowNeutral.map((item) => (
                  <div key={item.name} className="text-center">
                    <div
                      className="w-[100px] h-[100px] bg-white rounded-vsa-xl mb-3"
                      style={{ boxShadow: item.shadow }}
                    />
                    <code className="text-[11px] text-vsa-gray-600">{item.name}</code>
                  </div>
                ))}
              </div>
            </section>

            <section className="bg-white rounded-vsa-2xl p-8 shadow-vsa-sm">
              <h3 className="text-sm font-semibold text-vsa-gray-500 mb-6 uppercase tracking-wider">
                Sombras Coloridas (Glow Effect)
              </h3>
              <div className="flex gap-6 flex-wrap">
                {shadowColored.map((item) => (
                  <div key={item.name} className="text-center">
                    <div className={`w-[100px] h-[100px] rounded-vsa-xl mb-3 ${item.bgClass} ${item.className}`} />
                    <code className="text-[11px] text-vsa-gray-600">{item.name}</code>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
