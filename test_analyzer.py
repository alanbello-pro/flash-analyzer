# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2026 Alan Bello
# Descrição: Testes unitários para validar a arquitetura e componentes do flash-analyzer.

import os
import unittest
import tempfile
import io
import contextlib

from analyzer import (
    memory_sizes,
    analysis_summary,
    parsed_contributions,
    esp32_gcc_parser,
    report_summary
)

class TestMemorySizes(unittest.TestCase):
    def test_flash_size_calculation(self) -> None:
        sizes = memory_sizes(text=100, rodata=50, data=20, bss=200)
        self.assertEqual(sizes.flash_size, 170)

    def test_accumulate(self) -> None:
        sizes1 = memory_sizes(text=10, rodata=5, data=2, bss=50)
        sizes2 = memory_sizes(text=20, rodata=10, data=3, bss=100)
        sizes1.accumulate(sizes2)
        self.assertEqual(sizes1.text, 30)
        self.assertEqual(sizes1.rodata, 15)
        self.assertEqual(sizes1.data, 5)
        self.assertEqual(sizes1.bss, 150)

    def test_add_by_category(self) -> None:
        sizes = memory_sizes()
        sizes.add_by_category('text', 40)
        sizes.add_by_category('rodata', 30)
        sizes.add_by_category('data', 20)
        sizes.add_by_category('bss', 10)
        self.assertEqual(sizes.text, 40)
        self.assertEqual(sizes.rodata, 30)
        self.assertEqual(sizes.data, 20)
        self.assertEqual(sizes.bss, 10)

    def test_to_dict(self) -> None:
        sizes = memory_sizes(text=1, rodata=2, data=3, bss=4)
        self.assertEqual(sizes.to_dict(), {'text': 1, 'rodata': 2, 'data': 3, 'bss': 4})


class TestEsp32GccParser(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = esp32_gcc_parser()
        self.temp_map = tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8')
        
        map_content = """
Memory Configuration
Name             Origin             Length             Attributes
*default*        0x0000000000000000 0xffffffffffffffff

Linker script and memory map

 .flash.text    0x42000020         0x50 c:/Users/user/src/core/main.cpp.o
 .flash.text    0x42000070         0x30 c:/Users/user/src/components/sensor.cpp.o
 .flash.text    0x420000a0        0xf80 C:/Users/user/.platformio/packages/framework-espidf/libbt.a(bt_init.o)

 .dram0.data    0x3fc00000         0x20 c:/Users/user/src/core/main.cpp.o
 .dram0.data    0x3fc00020         0x80 C:/Users/user/.platformio/packages/framework-espidf/libbt.a(bt_init.o)

 .dram0.bss     0x3fc00100         0x50 c:/Users/user/src/core/main.cpp.o
        """
        self.temp_map.write(map_content)
        self.temp_map.close()

    def tearDown(self) -> None:
        os.unlink(self.temp_map.name)

    def test_parse_valid_content(self) -> None:
        result = self.parser.parse(self.temp_map.name)
        self.assertIsNotNone(result)
        
        self.assertIn('src/core', result.layers)
        self.assertIn('src/components', result.layers)
        self.assertIn('SDK/bt', result.layers)
        
        core_sizes = result.layers['src/core']
        self.assertEqual(core_sizes.text, 80)
        self.assertEqual(core_sizes.data, 32)
        self.assertEqual(core_sizes.bss, 80)

        bt_sizes = result.layers['SDK/bt']
        self.assertEqual(bt_sizes.text, 3968)
        self.assertEqual(bt_sizes.data, 128)

    def test_parse_non_existent_file(self) -> None:
        result = self.parser.parse("arquivo_que_nao_existe.map")
        self.assertIsNone(result)


class TestReporterDispatch(unittest.TestCase):
    def test_report_dispatch_json(self) -> None:
        sizes = memory_sizes(text=10, rodata=5, data=2, bss=50)
        summary = analysis_summary(
            env_name="test",
            firmware_bin_size=17,
            app_limit=1000,
            chip_limit=2000,
            layers={"src/core": sizes},
            sdk_data=memory_sizes(),
            file_details={}
        )
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            report_summary(summary, json_mode=True)
        output = f.getvalue()
        self.assertIn('"env": "test"', output)
        self.assertIn('"total_our_flash_bytes": 17', output)

    def test_report_dispatch_terminal(self) -> None:
        sizes = memory_sizes(text=10, rodata=5, data=2, bss=50)
        summary = analysis_summary(
            env_name="test",
            firmware_bin_size=17,
            app_limit=1000,
            chip_limit=2000,
            layers={"src/core": sizes},
            sdk_data=memory_sizes(),
            file_details={}
        )
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            report_summary(summary, json_mode=False)
        output = f.getvalue()
        self.assertIn("RELATORIO DE CONSUMO DE MEMORIA FLASH", output)
        self.assertIn("src/core", output)


if __name__ == '__main__':
    unittest.main()
