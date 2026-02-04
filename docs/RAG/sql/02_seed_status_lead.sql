-- Seed de status de lead (idempotente)

insert into public.status_lead (codigo, rotulo)
values
  ('novo',           'Novo'),
  ('qualificado',    'Qualificado'),
  ('desqualificado', 'Desqualificado'),
  ('negociacao',     'Negociação'),
  ('ganho',          'Ganho'),
  ('perdido',        'Perdido')
on conflict (codigo) do update set
  rotulo = excluded.rotulo;
