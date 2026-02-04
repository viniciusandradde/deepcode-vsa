-- Reset parcial do CRM para o curso (DROPs idempotentes)
-- Use quando houve tentativas anteriores e deseja recriar o schema do M1A

drop table if exists public.itens_proposta cascade;
drop table if exists public.propostas cascade;
drop table if exists public.tarefas_lead cascade;
drop table if exists public.notas_lead cascade;
drop table if exists public.leads cascade;
drop table if exists public.status_lead cascade;

