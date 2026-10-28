# Changelog

## [1.0.0]

### Adicionado
- Entrada e saída de visitantes com crachá automático e controle de lotação por setor.
- Lista de presentes com filtro, histórico com filtros e resumo por setor.
- Exportação do histórico para CSV (CPF mascarado, compatível com Excel).
- Ordenação do histórico pelo cabeçalho das colunas.
- Botão "Ver histórico" com as últimas cinco visitas de um CPF.
- Gestão de setores com exclusão protegida.
- Três temas (claro, escuro e institucional), lembrados entre execuções.
- Botão de saída que só habilita com uma visita selecionada.
- Ícones SVG próprios de entrada e saída.
- Gerador de dados fictícios com semente e testes automatizados.

### Corrigido
- CPF com todos os dígitos iguais (por exemplo 111.111.111-11) era aceito.
- Nome do visitante anterior permanecia no campo ao trocar de CPF.
- Com o banco indisponível, a troca de aba mostrava um alerta por tabela; agora mostra um só.

### Limitações conhecidas
- Um computador por vez acessando o banco.
- CPFs dos dados fictícios podem coincidir com CPFs reais por acaso.
- Fonte própria ainda não incluída (exige arquivo .ttf com licença de redistribuição).