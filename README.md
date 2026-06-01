# Sistema de Busca de Atestados (Brasul)

Sistema desktop para consulta e cadastro de códigos FDE, com base em Excel compartilhado na rede Brasul.

## Visão geral

- Produto: `Sistema de Busca de Atestados`
- Público: equipe de obras/cadastro
- Plataforma: Windows
- Atualização: padrão `current\` (fecha e abre o atalho)
- Fonte oficial: `Cofre_atestados_brasul.xlsx` (aba `Atestados de Obras` + `Base de Referência`)

## Estrutura de dados (oficial)

Todos os dados de operação ficam em:

`Z:\0 OBRAS\Sistema_de_atestado_brasul\DATA\`

```
DATA/
├── input/
│   └── Cofre_atestados_brasul.xlsx   # planilha mestre
├── output/
│   └── Cofre_Brasul.xlsx             # cópia para consulta
├── backup/                           # backups automáticos
└── logs/                             # logs de uso/cadastro
```

## Funcionalidades principais

- Busca por obra, código e descrição
- Filtros por tipo (`Acumulado` / `Quantitativa`)
- Filtro por data (`Data início` / `Data emissão TPR`)
- Colunas de data na tabela (com rolagem horizontal)
- Cadastro manual de atestado e inclusão de código na base de referência
- Sincronização em tempo real da planilha na rede
- Exportação do resultado filtrado para Excel

## Execução em desenvolvimento

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python src\interface.py
```

## Build e atualização na rede (`current`)

Fluxo padrão dos outros sistemas: build + release histórico + atualização de `current\`.

```powershell
.\ATUALIZAR_ATESTADO.bat
# ou
powershell -ExecutionPolicy Bypass -File tools\build_release.ps1
```

Saída do processo:

- `releases\Cofre_Brasul_v<versao>_<timestamp>\` (histórico)
- `current\` (versão ativa para usuários)

Atalho dos usuários:

- `Z:\0 OBRAS\Sistema_de_atestado_brasul\current\Cofre_Brasul.exe`

Regra operacional: após atualização, os usuários precisam apenas **fechar e abrir novamente** o programa.

## Configuração de ambiente

Ordem de resolução da pasta de dados:

1. Variável `COFRE_BRASUL_DATA`
2. Arquivo `deploy\rede.path`
3. Fallback local `.\DATA`

Exemplo de `deploy\rede.path`:

`Z:\0 OBRAS\Sistema_de_atestado_brasul\DATA`

## Uso local (sem rede, ex.: home office)

Sem acesso ao `Z:`, use `DATA` local:

```
DATA/
├── input/Cofre_atestados_brasul.xlsx
└── output/Cofre_Brasul.xlsx
```

Se não tiver `output\Cofre_Brasul.xlsx`, rode o sistema e clique em **Recarregar dados** para sincronizar a partir do `input`.

## Segurança de dados e Git

Dados da empresa **não** sobem para o Git:

- planilhas (`*.xlsx`, `*.xlsm`, `*.xls`)
- PDFs (`*.pdf`)
- pasta `DATA/` operacional
- logs de uso/cadastro
- `deploy/rede.path` real

Versionar somente código, scripts e documentação.

## Estrutura do projeto

```
.
├── assets/
├── config/
├── deploy/
├── docs/
├── scripts/
├── src/
├── tools/
├── ATUALIZAR_ATESTADO.bat
├── Brasul-BuscaAtestados.bat
├── Cofre_Brasul.spec
└── requirements.txt
```

## Observações operacionais

- Fechar Excel antes de gravar cadastro pelo sistema
- Evitar trabalhar em cópias paralelas da planilha mestre
- Em caso de erro de arquivo em uso no release, fechar o programa em todos os PCs e repetir
