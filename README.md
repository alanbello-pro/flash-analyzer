# Analisador de Consumo de Flash (GCC Linker Map Analyzer)

> Um processador de mapas de linkagem GCC (.map) de alta performance que calcula com precisão o consumo real de memória Flash em firmwares de microcontroladores.

[![Licença GPL-2.0](https://img.shields.io/badge/License-GPL--2.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#)
[![Status](https://img.shields.io/badge/Status-Estavel-green.svg)](#)

Esta ferramenta processa o arquivo de mapeamento (.map) gerado pelo linker GCC (ld) e calcula com precisão matemática o consumo real de memória Flash do firmware. Ela divide automaticamente a ocupação de cada arquivo objeto (.o) e biblioteca estática (.a) por diretórios e módulos dinâmicos, ordenados de forma decrescente de tamanho.

Desenvolvida puramente com a biblioteca padrão do Python 3, a ferramenta é totalmente independente de IDEs ou frameworks (como PlatformIO, ESP-IDF nativo, Arduino ou STM32CubeIDE), sendo compatível com qualquer firmware compilado sob arquiteturas Xtensa, ARM Cortex-M, AVR, RISC-V, entre outras.

---

## Indice

- [Recursos](#recursos)
- [Demonstracao Visual](#demonstracao-visual)
- [Requisitos](#requisitos)
- [Instalacao](#instalacao)
- [Como Usar](#como-usar)
- [Exemplos por Ecossistema](#exemplos-por-ecossistema)
- [Argumentos da CLI](#argumentos-da-cli)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Testes Automatizados](#testes-automatizados)
- [Detalhes Tecnicos](#detalhes-tecnicos)
- [Licenca](#licenca)
- [Autor](#autor)

---

## Recursos

* **Zero Dependencias Externas**: Funciona nativamente com qualquer instalação do Python 3.10 ou superior, sem necessidade de instalar pacotes via pip (como pandas, rich ou tabulate).
* **Filtro de Descarte Real do Linker**: Ignora automaticamente todas as seções marcadas com endereço de alocação nulo (0x00000000). Isso evita que seções de código mortas que foram otimizadas e removidas pelo compilador (via flags como --gc-sections) inflem os relatórios falsamente.
* **Auto-Grouping Dinamico**: Classifica e agrupa as contribuições físicas do firmware de forma inteligente:
  * Arquivos de código local (localizados sob pastas como /src/ ou similares) são agrupados por seus subdiretórios de origem.
  * Bibliotecas externas empacotadas (.a) são desmembradas e classificadas de forma amigável sob a categoria SDK/nome_da_biblioteca.
* **Metricas Relativas**: Exibe o consumo de Flash sob duas perspectivas: em relação ao limite lógico da partição de aplicação (app partition) e em relação ao tamanho do chip de memória física.
* **Relatorio JSON Integrado**: Retorna os dados consolidados em formato JSON padronizado com apenas um argumento, ideal para gerar relatórios automatizados ou integrar com pipelines de CI/CD.
* **Modo Comparativo (Delta)**: Permite comparar o build atual com um arquivo .map gerado em uma compilação anterior, listando a diferença exata de bytes por módulo para identificar onde o firmware cresceu ou reduziu.
* **Detalhamento Granular**: Exibe uma tabela com o Top 10 maiores arquivos consumidores de memória do firmware.
* **Arquitetura Desacoplada**: Desenvolvido sob os conceitos de Clean Architecture e padrões de projeto criacionais e comportamentais do GoF (Strategy e Factory) para facilitação de testes e extensibilidade.

---

## Demonstracao Visual

Abaixo está um exemplo da saída estruturada no terminal gerada pela ferramenta ao processar os limites de partição de aplicação e tamanho de chip físico, incluindo as molduras e a barra de progresso horizontal adaptável (com suporte nativo a sub-blocos UTF-8 e fallback para ASCII):

```text
$ python main.py --map firmware.map --bin firmware.bin --limit-app 1.875M --detail

┌─────────────────────────────────────────────────────────────────────┐
│  RELATORIO DE CONSUMO DE MEMORIA FLASH                              │
├─────────────────────────────────────────────────────────────────────┤
│  Ambiente: esp32dev                                                 │
│  Tamanho do Binario (.bin): 1.53 MB (1,604,320 bytes)               │
│  Limite Logico da Aplicacao: 1.88 MB (1,966,080 bytes)              │
│                                                                     │
│  Consumo de Particao App:                                           │
│  [████████████████████████████████░░░░░░░] 81.60%                   │
│                                                                     │
│  Capacidade do Chip Fisico (4.00 MB):                               │
│  [██████████████░░░░░░░░░░░░░░░░░░░░░░░░] 38.25%                    │
├─────────────────────────────────────────────────────────────────────┤
│  DISTRIBUICAO FISICA POR DIRETORIO / MODULO                         │
├─────────────────────────────────────────────────────────────────────┤
│  Modulo                       Tamanho (B)   Tamanho (KB)     % App  │
│  ─────────────────────────────────────────────────────────────────  │
│  SDK/esp_wifi                 422,240 B        412.3 KB      21.48% │
│  src/core                   322,048 B        314.5 KB      16.38%   │
│  SDK/lwip                   206,028 B        201.2 KB      10.48%   │
│  src/components             184,442 B        180.1 KB       9.38%   │
│  SDK/freertos               123,340 B        120.4 KB       6.27%   │
│  src/policies               102,400 B        100.0 KB       5.21%   │
│  Outros                     243,822 B        238.1 KB      12.41%   │
│  ─────────────────────────────────────────────────────────────────  │
│  CODIGO PROJETO             290,900 B        284.0 KB      14.80%   │
├─────────────────────────────────────────────────────────────────────┤
│  TOP 10 MAIORES ARQUIVOS OBJETO E BIBLIOTECAS (.a / .o)             │
├─────────────────────────────────────────────────────────────────────┤
│  Arquivo Objeto / Biblioteca                   Tamanho       % App  │
│  ─────────────────────────────────────────────────────────────────  │
│  1. SDK/esp_wifi/libnet80211.a                 214.5 KB      11.16% │
│  2. SDK/esp_wifi/libpp.a                       197.8 KB      10.30% │
│  3. src/core/robot_state.o                      84.2 KB       4.38% │
│  4. SDK/lwip/liblwip.a                          68.4 KB       3.56% │
│  5. src/components/sonar.o                      64.1 KB       3.34% │
│  6. SDK/freertos/tasks.o                        42.2 KB       2.20% │
│  7. src/components/motor.o                      38.1 KB       1.98% │
│  8. src/policies/navigation.o                  34.5 KB       1.80%  │
│  9. src/core/main.o                            28.4 KB       1.48%  │
│  10. Outros                                    412.0 KB      21.45% │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Requisitos

* Python 3.10 ou superior.
* Nenhuma dependência externa ou biblioteca de terceiros é necessária (Standard Library apenas).

---

## Instalacao

Para começar a usar a ferramenta, basta clonar o repositório em sua máquina:

```bash
git clone https://github.com/alanbello-pro/flash-analyzer.git
cd flash-analyzer
```

Como a ferramenta foi projetada de forma independente, você pode chamá-la de qualquer diretório referenciando o arquivo `main.py`.

---

## Como Usar

Execute o script passando o caminho do arquivo `.map` gerado pela compilação do seu projeto:

```powershell
python main.py --map caminho/do/linker_map.map --bin caminho/do/firmware.bin --limit-app 1.5M --detail
```

---

## Exemplos por Ecossistema

### PlatformIO (ESP32)
No PlatformIO, os artefatos de build residem na pasta oculta `.pio/build/<ambiente>`.

Você pode executar o analisador chamando o comando instalado diretamente no seu terminal:
```powershell
flash-analyzer --map .pio/build/esp32dev/firmware.map --bin .pio/build/esp32dev/firmware.bin --limit-app 1.875M --detail
```

Ou rodando o script `main.py` diretamente com o interpretador Python:
```powershell
python main.py --map .pio/build/esp32dev/firmware.map --bin .pio/build/esp32dev/firmware.bin --limit-app 1.875M --detail
```

---

## Argumentos da CLI

| Parametro | Tipo | Descricao | Exemplo |
|---|---|---|---|
| `-m`, `--map` | Caminho | **Obrigatorio**. Caminho do arquivo `.map` do linker. | `--map build/app.map` |
| `-a`, `--arch` | String | Opcional. Compilador/Arquitetura do mapa de memória (Padrão: `esp32-gcc`). | `--arch esp32-gcc` |
| `-b`, `--bin` | Caminho | Opcional. Caminho do binário final `.bin` para exibir tamanho físico real. | `--bin build/app.bin` |
| `-la`, `--limit-app` | Tamanho | Opcional. Limite da partição de aplicação (aceita `M`, `K` ou bytes. Padrao: `1.5M`). | `--limit-app 1.8M` |
| `-lc`, `--limit-chip` | Tamanho | Opcional. Capacidade total de Flash do chip físico (aceita `M`, `K` ou bytes. Padrao: `4M`). | `--limit-chip 8M` |
| `-e`, `--env` | String | Opcional. Identificador do ambiente do build exibido no cabeçalho do relatorio. | `--env esp32dev` |
| `-d`, `--detail` | Flag | Exibe o Top 10 maiores arquivos do projeto consumidores de memória. | `--detail` |
| `-j`, `--json` | Flag | Retorna os dados estruturados em JSON para integrações de scripts externos ou CI. | `--json` |
| `-c`, `--compare` | Caminho | Compara com outro mapa de linker antigo e mostra a diferença em bytes por módulo. | `--compare old.map` |

---

## Estrutura do Projeto

* [main.py](main.py): Ponto de entrada CLI e *wiring* (injeção de dependências) da ferramenta. Totalmente desacoplado de lógicas de parsing ou formatação física de arquivos.
* [domain.py](domain.py): Camada de Domínio Puro. Contém as entidades logicamente puras e ricas (`MemorySizes` e `AnalysisSummary`) que tratam do cálculo de bytes físicos de memória.
* [parser.py](parser.py): Camada de Adaptadores. Contém a interface abstrata `LinkerMapParser` e as implementações concretas (`Esp32GccParser`) de parsing sequencial baseadas no padrão **Strategy** e **Factory** (`ParserFactory`).
* [reporter.py](reporter.py): Camada de Apresentadores. Contém a interface `Reporter` e as implementações de relatórios (`TerminalTableReporter`, `JsonReporter`) no padrão **Strategy** e **Factory** (`ReporterFactory`).
* [config.py](config.py): Contém constantes padrões de limite e a lógica utilitária pura de parsing de limites em bytes da CLI.

---

## Testes Automatizados

A ferramenta conta com uma suíte de testes unitários automatizados para garantir a robustez de futuras extensões e prevenir regressões lógicas em modificações de exibição ou regras de agrupamento.

Para executar todos os testes locais, utilize o interpretador Python chamando o módulo de testes nativo:

```bash
python -m unittest test_analyzer.py
```

Os testes cobrem:
* **Cálculo de Flash Ativo:** Garantia de isolamento e soma das seções de Flash `.text`, `.rodata` e `.data` descartando seções de RAM `.bss`.
* **Acumulação de Segmentos:** Validação de comportamento da entidade de domínio `MemorySizes` e sua lógica de agregação.
* **Parsing de Mapa Simulador:** Leitura física e aplicação de expressões regulares contra arquivos de mapa sintéticos criados dinamicamente em arquivos temporários.
* **Fábricas de Dependências:** Validação de injeção polimórfica das classes de Parser e Reporter via `ParserFactory` e `ReporterFactory`.

---

## Detalhes Tecnicos

Diferente de analisadores baseados em ler os símbolos brutos das tabelas ELF do binário (que mostram apenas funções individuais), este analisador examina a saída do mapeamento do linker. O linker GCC gera logs estruturados no arquivo `.map` detalhando quais arquivos objeto e seções foram unificados na memória.

O script varre sequencialmente as linhas do arquivo buscando definições de seções de memória como `.text`, `.rodata` e `.data` e mapeando o local exato do arquivo físico que gerou a inclusão. Linhas indicando endereços de carga iguais a zero (como `0x00000000`) representam funções e objetos que foram marcados para descarte por não serem referenciados no código principal. Descartar essas entradas é o que garante que o cálculo total de memória coincida exatamente com o tamanho do binário físico gravado no microcontrolador.

---

## Licenca

Este projeto está licenciado sob os termos da licença **GNU General Public License v2.0** (GPL-2.0-only). Consulte o arquivo [LICENSE](LICENSE) para obter o texto completo da licença.

---

## Autor

Desenvolvido por **Alan Bello**, com foco em engenharia reversa e otimização de sistemas embarcados limpos.
