import unittest
from opaflib.lexer import tokens, LexerException, get_lexer, lexify

class ParserTest(unittest.TestCase):
    def setUp(self):
        self.my_lexer = get_lexer()
    def tearDown(self):
        pass

    def testLexer(self):
        self.assertEqual("[LexToken(NUMBER,'1',1,0)]", str(lexify('1')) )


        

if __name__ == '__main__':
    unittest.main()

        


