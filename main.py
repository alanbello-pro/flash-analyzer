# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 Alan Bello
# Descrição: Ponto de entrada CLI e orquestrador da ferramenta de análise de Flash.

import os
import sys
import argparse

from analyzer import (
    analysis_summary,
    esp32_gcc_parser,
    report_summary,
    print_compare,
    parse_size_limit,
    ESP32_APP_LIMIT,
    ESP32_FLASH_LIMIT,
    RED,
    RESET
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisador de Consumo de Flash (GCC Linker Map Analyzer)"
    )
    parser.add_argument(
        '-m', '--map',
        required=True,
        help="Caminho do arquivo .map do linker (obrigatorio)"
    )
    parser.add_argument(
        '-a', '--arch',
        default='esp32-gcc',
        help="Arquitetura/Compilador do mapa de memoria (padrao: esp32-gcc)"
    )
    parser.add_argument(
        '-b', '--bin',
        help="Caminho para o arquivo .bin correspondente (opcional)"
    )
    parser.add_argument(
        '-la', '--limit-app',
        default='1.5M',
        help="Limite da particao de aplicacao, ex: 1.5M, 1024K (padrao: 1.5M)"
    )
    parser.add_argument(
        '-lc', '--limit-chip',
        default='4M',
        help="Limite fisico do chip de Flash, ex: 4M, 8M (padrao: 4M)"
    )
    parser.add_argument(
        '-e', '--env',
        default='default',
        help="Identificador do ambiente de build (padrao: default)"
    )
    parser.add_argument(
        '-d', '--detail',
        action='store_true',
        help="Exibe o Top 10 maiores arquivos consumidores de memoria do projeto"
    )
    parser.add_argument(
        '-j', '--json',
        action='store_true',
        help="Retorna os dados estruturados em JSON para CI/CD"
    )
    parser.add_argument(
        '-c', '--compare',
        help="Compara o build atual com um arquivo .map antigo"
    )
    return parser.parse_args()


def run_flash_analysis() -> None:
    args = parse_arguments()
    map_file = args.map

    if not os.path.exists(map_file):
        print(f"{RED}Erro: Arquivo do mapa do linker '{map_file}' nao encontrado.{RESET}")
        sys.exit(1)

    app_limit = parse_size_limit(args.limit_app, default_limit=ESP32_APP_LIMIT)
    chip_limit = parse_size_limit(args.limit_chip, default_limit=ESP32_FLASH_LIMIT)

    parser = esp32_gcc_parser()
    parse_result = parser.parse(map_file)
    if parse_result is None:
        print(f"{RED}Erro ao parsear arquivo map em {map_file}.{RESET}")
        sys.exit(1)

    total_detected = sum(s.flash_size for s in parse_result.layers.values()) + parse_result.sdk_data.flash_size
    if total_detected == 0:
        from analyzer import YELLOW
        print(f"{YELLOW}Aviso: Nenhuma secao de memoria activa detectada no mapa '{map_file}'.")
        print(f"Verifique se o arquivo esta vazio ou se possui formato incompativel com o padrão do ESP32 GCC.{RESET}")
        sys.exit(1)

    bin_file = args.bin
    firmware_bin_size = os.path.getsize(bin_file) if bin_file and os.path.exists(bin_file) else 0

    file_details_to_pass = parse_result.file_details if args.detail else None
    summary = analysis_summary(
        env_name=args.env,
        firmware_bin_size=firmware_bin_size,
        app_limit=app_limit,
        chip_limit=chip_limit,
        layers=parse_result.layers,
        sdk_data=parse_result.sdk_data,
        file_details=file_details_to_pass
    )

    report_summary(summary, args.json)

    compare_file = args.compare
    if compare_file and not args.json:
        prev_result = parser.parse(compare_file)
        if not prev_result:
            print(f"{RED}Erro: Nao foi possivel parsear arquivo de comparacao '{compare_file}'{RESET}")
            return
            
        print_compare(summary, prev_result)


if __name__ == '__main__':
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
    run_flash_analysis()
