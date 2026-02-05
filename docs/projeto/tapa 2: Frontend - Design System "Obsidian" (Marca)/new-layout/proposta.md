O objetivo é sair de uma "Ferramenta de Admin" para um "Cockpit de Comando".

A. Estética "Glass-Shell" Imersiva (Obsidian v2.0)
Implementar o conceito aprovado de Deep Void com as cores da marca (Laranja/Azul).

Layout App-Like: O corpo da página (body) deve ser overflow: hidden. Apenas os containers de conteúdo (Chat, Tabelas) devem ter scroll. Isso dá a sensação de aplicativo nativo, não de site.

Vidro Fosco Dinâmico: Utilizar backdrop-filter: blur(20px) com uma textura de ruído (noise texture) em 2% de opacidade sobre os painéis. Isso evita o aspecto "plástico" e adiciona textura premium.

Ambient Lighting (Luz Ambiente): Usar orbs de luz difusa (Laranja no canto superior esquerdo, Azul no inferior direito) fixos no fundo, movendo-se muito lentamente (animação CSS float) para dar vida ao fundo preto.

B. Micro-interações e Feedback Tátil
Uma aplicação empresarial deve parecer "viva".

Hover States Avançados: Botões não mudam apenas de cor. Eles devem ter um leve scale(1.02) e um aumento no box-shadow (Glow) da cor correspondente (Laranja ou Azul).

Skeleton Screens: Nunca use spinners de carregamento para áreas grandes. Use "Skeletons" (barras pulsantes cinza-escuro) que imitam o layout do conteúdo que está por vir (tabelas, textos). Isso reduz a ansiedade de espera.

Transições de Rota: Implementar Framer Motion para que, ao trocar de aba na Sidebar, o conteúdo antigo desapareça suavemente e o novo deslize para dentro.

C. Command Palette (Cmd+K)
Recurso essencial em ferramentas modernas (como Linear, Vercel, VS Code).

Implementar um modal de busca global acessível por Ctrl+K ou Cmd+K.

Permite navegar entre projetos, buscar issues do Linear, iniciar um novo chat ou mudar o tema sem tirar a mão do teclado.

1. Propostas de Melhoria de Performance (Engenharia)
A. Frontend: Virtualização e Optimistic UI
O chat e as tabelas de relatórios podem ficar pesados com muitos dados.

Virtualização de Listas: Usar react-virtuoso ou tanstack-virtual nas janelas de chat. Isso renderiza apenas as mensagens visíveis na tela, permitindo chats com 10.000 mensagens sem travar o navegador.

Optimistic Updates: Quando o usuário enviar uma mensagem ou editar uma issue, a interface deve atualizar instantaneamente, antes mesmo da resposta do servidor. Se der erro, reverte-se com um Toast de aviso.

Code Splitting Agressivo: Garantir que bibliotecas pesadas (como gráficos ou editores de código) sejam carregadas via dynamic imports do Next.js apenas quando necessárias.
