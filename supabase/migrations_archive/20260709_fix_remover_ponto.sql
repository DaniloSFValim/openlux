-- Atualiza ip_remover_ponto: remove a dependência da fila_aprovacao
-- (fluxo de aprovações foi descontinuado — editores agem diretamente,
-- mesma decisão aplicada à edição no PR #8).
--
-- Comportamento:
--   - leitura / não autenticado: bloqueado
--   - editor e admin: exclusão imediata, sempre com backup completo
--     do registro em ativos_removidos (dados_backup jsonb, autor, motivo)
--   - o trigger de histórico registra a operação DELETE

create or replace function public.ip_remover_ponto(p_id uuid, p_motivo text default null)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_user_id uuid;
  v_ponto jsonb;
  v_role text;
begin
  v_user_id := auth.uid();
  if v_user_id is null then
    return jsonb_build_object('error', 'Não autenticado');
  end if;

  select role into v_role from profiles where id = v_user_id;
  if v_role is null or v_role = 'leitura' then
    return jsonb_build_object('error', 'Sem permissão para remover ativos');
  end if;

  select to_jsonb(p.*) into v_ponto from v_parque_export p where id = p_id;
  if v_ponto is null then
    return jsonb_build_object('error', 'Ponto não encontrado');
  end if;

  -- Backup completo antes da exclusão (permite restauração futura)
  insert into ativos_removidos (ponto_id, dados_backup, removido_por, motivo)
  values (p_id, v_ponto, v_user_id, p_motivo);

  delete from v_parque_export where id = p_id;

  return jsonb_build_object('success', true, 'message', 'Ativo removido');
end;
$$;
