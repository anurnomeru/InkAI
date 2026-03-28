import os
import json
import tempfile
import shutil
import unittest

import sys
sys.path.insert(0, os.path.abspath('.'))

from config_manager import load_config, save_config, DEFAULT_CONFIG

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix='cfgtest_')
        self.cfg = os.path.join(self.tmpdir, 'config.json')

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def read_json(self):
        with open(self.cfg, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_create_when_missing(self):
        data = load_config(self.cfg)
        self.assertIn('llm_configs', data)
        self.assertTrue(isinstance(data['llm_configs'], dict) and data['llm_configs'])
        for key in ('prompt_draft_llm','chapter_outline_llm','architecture_llm','final_chapter_llm','consistency_review_llm'):
            self.assertIn(key, data['choose_configs'])
            self.assertIn(data['choose_configs'][key], data['llm_configs'])

    def test_self_heal_missing_top_keys(self):
        with open(self.cfg, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        data = load_config(self.cfg)
        for k in DEFAULT_CONFIG.keys():
            self.assertIn(k, data)

    def test_self_heal_missing_llm_and_choose(self):
        bad = dict(DEFAULT_CONFIG)
        bad.pop('llm_configs', None)
        bad['choose_configs'] = { 'prompt_draft_llm': 'DeepSeek V3' }
        with open(self.cfg, 'w', encoding='utf-8') as f:
            json.dump(bad, f, ensure_ascii=False)
        data = load_config(self.cfg)
        # choose 引用的 llm 名称必须存在
        name = data['choose_configs']['prompt_draft_llm']
        self.assertIn(name, data['llm_configs'])

    def test_invalid_json_backup(self):
        with open(self.cfg, 'w', encoding='utf-8') as f:
            f.write('{ invalid json ')
        data = load_config(self.cfg)
        self.assertIn('llm_configs', data)
        # 备份文件应存在
        backups = [fn for fn in os.listdir(self.tmpdir) if fn.startswith('config.json.') and fn.endswith('.bak')]
        self.assertTrue(backups)

if __name__ == '__main__':
    unittest.main()
