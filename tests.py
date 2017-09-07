import unittest

import lib.test_bot as tb


class TestTextChecker(unittest.TestCase):

    def test_text_is_start_command(self):
        text = '/start'
        self.assertIn('Добро пожаловать', tb.checkText(text))

    def test_text_is_help_command(self):
        text = '/help'
        self.assertIn('Доступные команды', tb.checkText(text))

    def test_text_is_getcn_command(self):
        text = '/get_by_cn 61:01:123456:123'
        cn = '61:01:123456:123'
        self.assertEqual(tb.checkText(text), tb.get_by_cn(cn))

    def test_text_is_getcn_without_cn(self):
        text = '/get_by_cn '
        self.assertIn('Не введен', tb.checkText(text))

    def test_text_is_cn(self):
        text = '61:01:123456:123'
        self.assertEqual(tb.checkText(text), tb.get_by_cn(text))

    def test_text_is_notcommand(self):
        """input is a wrong text"""
        text = 'h..some text here'
        self.assertIn('не верная команда', tb.checkText(text))

    def test_cn_is_not_cn(self):
        """Getted text isn't cn"""
        text = '/get_by_cn 61:pp:10230422:434:32'
        self.assertIn('Не введен', tb.checkText(text))


class TestCNPrepare(unittest.TestCase):

    def test_cn_is_61_00_000000000000_00000(self):
        """Getted cn with all 0"""
        text = '00:00:000000000:000000'
        self.assertEqual(tb.prepareCN(text), '0:0:0:0')

    def test_cn_is_61_01_0043432_123(self):
        text = '61:01:0043432:123'
        self.assertEqual(tb.prepareCN(text), '61:1:43432:123')



if __name__ == '__main__':
    unittest.main()
