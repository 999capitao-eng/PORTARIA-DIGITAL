# Desafio 06: plano de anonimização (LGPD, Lei 13.709/2018)

Situação: um titular pede a eliminação dos seus dados. Este é um **plano**, ainda não implementado.

| Local | Referência ao visitante? | Mudança necessária |
|---|---|---|
| `schema.sql` | Sim: `visitante.nome` e `visitante.documento` (UNIQUE) | Não apagar a linha, porque `visita` tem chave estrangeira e o histórico estatístico deve ser preservado. Substituir `nome` por `[anonimizado]` e `documento` por um marcador único, como `ANON-<id>`, que mantém o UNIQUE sem colidir com CPFs reais. Avaliar uma coluna `anonimizado_em` para auditoria. |
| `repositorio.py` | Sim, por consultas que devolvem nome e documento | Nova função `anonimizar_visitante(conn, visitante_id, marcador)` com `UPDATE` parametrizado. Sem commit, como as demais. |
| `servicos.py` | Sim | Regra: recusar se houver visita aberta (`saida IS NULL`), pois a lista de evacuação precisa dos dados. Tudo numa transação (`with conn:`). Lançar `RegraNegocioError` com mensagem clara. |
| Interface | Sim | Ação na aba de visitantes ou histórico, com confirmação explícita (`QMessageBox.question`) mostrando o CPF mascarado. Restringir a quem tem essa atribuição. |
| Log (`portaria.log`) | A verificar | Conferir se alguma mensagem registra nome ou CPF. A regra da casa é não registrar dados pessoais, só nomes de funções e tipos de erro. Se houver ocorrências antigas, definir rotação e retenção do log. |
| Testes | Sim | Provar que: (1) após anonimizar, nome e documento originais não aparecem em nenhuma consulta; (2) as visitas e o resumo por setor continuam iguais; (3) quem está no prédio não pode ser anonimizado; (4) um novo cadastro com o mesmo CPF volta a funcionar. |
| Arquivos exportados (Desafio 01) | Sim: o CSV traz o nome (o CPF sai mascarado) | A cópia fora do banco não é alcançada pelo `UPDATE`. Definir o procedimento: registrar onde os CSV são guardados, orientar a apagá-los ou regenerá-los após a anonimização e evitar enviá-los por canais sem controle. |

## Conclusão

Privacidade é requisito de arquitetura: o dado existe em várias cópias (tabela, log, exportações, backups do banco) e o plano precisa cobrir todas elas, não só a tabela principal.