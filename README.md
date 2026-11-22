# LLM - Investigador Criminal

Análise de padrões nos dados criminais do Brasil, com uma camada de GenAI que responde perguntas em português consultando o banco de dados (text-to-SQL).

> Projeto em desenvolvimento. Este README descreve o que já existe e o que está planejado.

## Proposta

O projeto tem duas partes:

1. **Análise de padrões.** Os dados do Sinesp VDE (Ministério da Justiça e Segurança Pública) são cruzados por município, UF e grande região. Comparações entre lugares usam taxas por 100 mil habitantes, e não contagens brutas. As análises previstas são:
   - sazonalidade mensal;
   - rankings de UFs e municípios;
   - correlação entre as séries mensais de UFs e regiões;
   - agrupamento (clusterização) de UFs ou municípios por perfil criminal;
   - detecção de meses ou locais atípicos.
2. **Chat com o banco (text-to-SQL).** A pessoa faz uma pergunta em português, por exemplo "qual região teve a maior taxa de homicídio doloso?". Então:
   - um LLM, acessado pela API do Hugging Face, recebe a pergunta e uma descrição do banco, e escreve uma consulta SQL;
   - a consulta roda no SQLite em modo somente leitura, aceitando apenas `SELECT`;
   - o LLM explica o resultado em português.

   O LLM não é treinado neste projeto: um modelo pronto é usado, e o trabalho está em descrever bem os dados, limitar o que ele pode executar e medir quantas perguntas ele acerta.

## Status

| Etapa | Situação |
|---|---|
| Carga do Excel no SQLite (`src/carga.py`) | feito |
| Notebook 01: exploração do banco | feito |
| Notebook 02: região e população do IBGE | feito |
| Notebook 03: variação mensal, rankings por taxa e correlações | feito |
| Notebook 04: clusterização e detecção de atípicos | planejado |
| Camada GenAI (text-to-SQL) | planejado |
| Avaliação com cerca de 20 perguntas de referência | planejado |
| Demo no Hugging Face Spaces (Gradio) | planejado |

## Estrutura

```
chat-investigador/
├── data/
│   ├── raw/
│   │   ├── BancoVDE 2026.xlsx                    dados do Sinesp VDE (jan a out de 2026)
│   │   └── ibge_municipios_populacao_2026.csv    cópia do que foi baixado do IBGE (gerada pelo notebook 02)
│   └── db/
│       └── crimes.db                             banco SQLite (gerado, fora do Git)
├── notebooks/
│   ├── exploracao_01.ipynb                       tamanho, eventos, nulos, cobertura, homônimos
│   ├── populacao_02.ipynb                        região, população e primeiras taxas
│   └── padroes_03.ipynb                          variação mensal, rankings e correlações
├── src/
│   └── carga.py                                  lê o Excel, limpa e grava a tabela ocorrencias
└── README.md
```

## Como reproduzir

Requer Python 3.12 e acesso à internet (para a API do IBGE).

```bash
python -m venv venv
source venv/bin/activate
pip install pandas requests openpyxl ipykernel matplotlib
python src/carga.py
```

Depois, rode os notebooks em ordem: o `populacao_02.ipynb` cria as tabelas `municipios` e `ufs` no banco. O `carga.py` substitui apenas a tabela `ocorrencias`, então as outras tabelas continuam no banco se a carga for refeita.

## Fontes de dados

| Fonte | O que traz | Como é obtida |
|---|---|---|
| Sinesp VDE 2026, Ministério da Justiça e Segurança Pública | ocorrências e vítimas por município, mês e evento | arquivo `BancoVDE 2026.xlsx` em `data/raw` |
| IBGE, API de Localidades | municípios com código, UF e grande região | `servicodados.ibge.gov.br/api/v1/localidades/municipios` |
| IBGE, Estimativas da População 2026 (agregado 6579, variável 9324) | população residente estimada em 1º de julho de 2026 | `servicodados.ibge.gov.br/api/v3/agregados/6579` |

## Dicionário de dados

O banco `data/db/crimes.db` tem três tabelas.

### `ocorrencias`

Uma linha por município, mês, evento e abrangência. Alguns eventos têm linhas a mais, abertas por agente, arma ou faixa etária. 675.482 linhas. Gerada por `src/carga.py`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `uf` | texto | Sigla da UF (27 valores). |
| `municipio` | texto | Nome do município em maiúsculas, como escrito no Sinesp. Vale `NÃO INFORMADO` nos eventos que só existem por estado e nos casos sem município. Há nomes repetidos em UFs diferentes, então use sempre junto com `uf`. |
| `evento` | texto | Tipo de evento (31 valores), por exemplo `Homicídio doloso`, `Feminicídio`, `Roubo de veículo`, `Apreensão de Cocaína`. |
| `metrica` | texto | O que o número da linha significa. `vítimas` são pessoas atingidas (coluna `total_vitima` do Excel). `total` são ocorrências ou procedimentos, conforme o evento (coluna `total`). `peso` vale para as apreensões de drogas (coluna `total_peso`). Cada evento tem uma única métrica. |
| `ano` | inteiro | Ano de referência (só 2026). |
| `mes` | inteiro | Mês de referência (1 a 10). |
| `data_referencia` | texto | Primeiro dia do mês de referência, no formato `AAAA-MM-DD`. |
| `abrangencia` | texto | Quem registrou: `Estadual`, `Polícia Federal` ou `Polícia Rodoviária Federal`. Um mesmo evento pode ter mais de uma abrangência; não some abrangências sem decidir isso de propósito. |
| `agente` | texto | Categoria do agente do Estado (por exemplo `Polícia Militar`). Só em `Morte de Agente do Estado` e `Suicídio de Agente do Estado`; nulo nos demais. |
| `arma` | texto | Tipo de arma (por exemplo `Pistola`). Só em `Arma de Fogo Apreendida`; nulo nos demais. |
| `faixa_etaria` | texto | `Maior de Idade`, `Menor de Idade` ou `Idade Não Informada`. Só em `Pessoa Desaparecida` e `Pessoa Localizada`; nulo nos demais. |
| `feminino` | inteiro | Vítimas do sexo feminino. Só em eventos com `metrica = 'vítimas'`, e nem sempre preenchido. |
| `masculino` | inteiro | Vítimas do sexo masculino. Mesmas condições de `feminino`. |
| `nao_informado` | inteiro | Vítimas sem sexo informado. Quando as três colunas de sexo estão preenchidas, a soma delas é igual a `quantidade`. |
| `quantidade` | inteiro | Número de vítimas ou de ocorrências, conforme `metrica`. Nulo nas apreensões de drogas. |
| `peso` | real | Peso apreendido de cocaína ou maconha. A unidade não é informada no arquivo de origem. Nulo nos demais eventos. |

### `municipios`

Uma linha por município do IBGE (5.571 linhas). Gerada pelo notebook `populacao_02.ipynb`. Liga com `ocorrencias` pelo par `(uf, municipio)`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `uf` | texto | Sigla da UF. |
| `municipio` | texto | Nome em maiúsculas, escrito como no Sinesp, para a junção com `ocorrencias`. Seis nomes foram ajustados porque a grafia difere entre IBGE e Sinesp (por exemplo, `ASSÚ` no IBGE e `AÇU` no Sinesp). |
| `nome_ibge` | texto | Nome oficial do município no IBGE. |
| `codigo_ibge` | texto | Código IBGE de 7 dígitos. |
| `regiao` | texto | Grande região: `Norte`, `Nordeste`, `Centro-Oeste`, `Sudeste` ou `Sul`. |
| `populacao` | inteiro | População residente estimada pelo IBGE para 2026. |

### `ufs`

Uma linha por UF (27 linhas). Gerada pelo notebook `populacao_02.ipynb`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `uf` | texto | Sigla da UF. |
| `nome_uf` | texto | Nome por extenso (por exemplo `Rio Grande do Norte`). |
| `regiao` | texto | Grande região. |
| `populacao` | inteiro | População estimada de 2026: a soma dos municípios, que confere com o total que o IBGE publica para a UF. |

## Cuidados com os dados

Estes pontos foram confirmados nos notebooks 01 e 02 e valem para qualquer análise ou consulta:

- **Métricas diferentes.** `quantidade` conta vítimas em alguns eventos e ocorrências em outros; as apreensões de drogas usam `peso`. Não some eventos com métricas diferentes.
- **Abrangência.** Filtre sempre por `abrangencia`. Os eventos da Polícia Rodoviária Federal param em maio ou agosto, e `Mortes no trânsito` da Polícia Federal só tem 4 meses.
- **Nível geográfico.** Só 12 das 43 combinações de evento e abrangência são abertas por município. Estupro, roubo e furto de veículo, tráfico e apreensões existem apenas por UF.
- **Cobertura.** Algumas UFs não informam certos eventos. Por exemplo, MG e RJ não informam apreensão de drogas (Estadual), e RO não informa os eventos de bombeiros. Ausência de linha significa "não informado", não zero.
- **Zeros.** Nos eventos municipais, a base traz uma linha para cada município em cada mês, inclusive com zero: 82% das linhas de homicídio doloso são zero. Por isso, taxas de municípios pequenos oscilam muito.
- **Homônimos.** 232 nomes de município aparecem em mais de uma UF. Use sempre `uf` junto com `municipio`.
- **Distrito Federal.** O DF aparece só como `BRASÍLIA` e `NÃO INFORMADO`; linhas repetidas de Brasília foram somadas na carga.
- **Taxas.** A taxa é `casos * 100000.0 / populacao`. O período é de jan a out de 2026, então as taxas não são anuais. Em SQL, agregue `ocorrencias` antes de juntar com `ufs` ou `municipios`; caso contrário, a população é somada uma vez por linha e o resultado sai errado.
- **Revisão.** Os dados estão sujeitos a revisão pelas UFs, e vários eventos estaduais têm menos UFs informando nos meses mais recentes.
- **Interpretação.** Diferenças entre lugares podem vir de diferenças na forma de registrar, e não só de diferenças reais. Correlação entre séries não indica causa.
