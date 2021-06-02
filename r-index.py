#!/usr/bin/python3

# Reverse index
# Copyright © 2021 Alberto Oporto
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from io import TextIOWrapper
from nltk.stem import SnowballStemmer
from subprocess import Popen, PIPE
from sys import argv, stdout, stdin
from typing import Counter, Dict, List, Set, TextIO

import readline

r_index: Dict[str, Set[str]] = {}

reserved = {
    'AND' : 'AND',
    'OR' : 'OR',
    'NOT' : 'NOT'
}


tokens = [
    'WORD',
] + list(reserved.values())


literals = "()"
t_ignore = " \t\n\r"
t_WORD = r'[a-zA-Z_\.]+'


def t_ID(t):
    r'[a-zA-Z]+'
    if t.value in reserved:
        t.type = reserved[t.value]
    else:
        t.type = 'WORD'
    return t

def t_error(t):
    print("Bad token '%s'" % t.value[0])
    t.lexer.skip(1)

import ply.lex as lex
lexer = lex.lex()

precedence: List[List] = [
    ['left', 'AND', 'OR', 'NOT']
]


def p_expr_expr(p):
    ''' expr : '(' expr ')'
    '''
    p[0] = p[2]

def p_expr_op(p):
    ''' expr : expr op expr
    '''
    if p[2] == 'AND':
        p[0] = AND(p[1], p[3])
    elif p[2] == 'OR':
        p[0] = OR(p[1], p[3])
    elif p[2] == 'AND NOT':
        p[0] = AND_NOT(p[1], p[3])


def p_expr_name(p):
    ''' expr : WORD
    '''
    p[0] = L(p[1])


def p_op_and(p):
    ''' op : AND
    '''
    p[0] = "AND"


def p_op_or(p):
    ''' op : OR
    '''
    p[0] = "OR"

def p_op_and_not(p):
    ''' op : AND NOT
    '''
    p[0] = "AND NOT"

def p_error(p):
    print("Yacc errror", p)

import ply.yacc as yacc
parser = yacc.yacc()


class word_completer:
    def __init__(self, words: List[str]) -> None:
        self.words: List = words

    def completer(self, text: str, state: int) -> str:
        match = [word for word in self.words if word.startswith(text)] + [None]
        return match[state]


def main() -> None:
    global r_index
    r_index_file = 'r_index.txt'

    if len(argv) > 1:
        with open(r_index_file, 'w') as output:
            generate_r_index(argv[1:], output)
    else:
        with open(r_index_file, 'r') as input_file:
            r_index = read_r_index(input_file)

        completer: word_completer = word_completer(list(reserved.values()) + list(r_index.keys()))

        readline.parse_and_bind("tab: complete")
        readline.set_completer(completer.completer)
        while True:
            try:
                execute_string(input('> '))
            except EOFError:
                break
            except KeyboardInterrupt:
                break
        print()


def execute_string(expression: str) -> None:
    lexer.input(expression)
    print(parser.parse())
    parser.restart()


def L(word: str) -> Set[str]:
    return set(r_index.get(word, []))


def AND(l: Set[str], r: Set[str]) -> Set[str]:
    return l.intersection(r)


def OR(l: Set[str], r: Set[str]) -> Set[str]:
    return l.union(r)


def AND_NOT(l: Set[str], r: Set[str]) -> Set[str]:
    return l.difference(r)


def generate_r_index(files: List[str], output: TextIO = stdout) -> None:
    words: List[str] = []
    r_index: Dict[str, Set[str]] = {}

    for file_name in files:
        with open(file_name, "r") as file:
            tokens: List[str] = preproccess(file)
            words.extend(tokens)
            for word in tokens:
                r_index.setdefault(word, set()).add(file_name)

    print_r_index(filter_r_index(r_index, words, 500), output)


def filter_r_index(r_index: Dict[str, Set[str]], words: List[str], n: int) -> Dict[str, Set[str]]:
    new_r_index: Dict[str, Set[str]] = {}
    for word in Counter(words).most_common(n):
        new_r_index[word[0]] = r_index[word[0]]
    return new_r_index


def print_r_index(r_index: Dict[str, Set[str]], file: TextIO = stdout) -> None:
    for word in sorted(r_index):
        print(word, end=":", file=file)
        print(','.join(sorted(r_index[word])), file=file)


def read_r_index(file: TextIO = stdin) -> Dict[str, Set[str]]:
    r_index: Dict[str, Set[str]] = {}

    for line in file:
        word_files = line.strip('\n').split(':', 1)
        r_index[word_files[0]] = set(word_files[1].split(','))

    return r_index


def preproccess(file: TextIOWrapper) -> List[str]:
    ss = SnowballStemmer("spanish")

    tr1 = Popen(['tr', '-s', '[:punct:][:space:]', '\n'], stdin=file, stdout=PIPE)
    tr2 = Popen(['tr', '[:upper:]', '[:lower:]'], stdin=tr1.stdout, stdout=PIPE)
    grep = Popen(['grep', '-Fvwf', 'stoplist.txt'], stdin=tr2.stdout, stdout=PIPE)

    tr1.stdout.close()
    tr2.stdout.close()

    words: List[str] = []
    for word in grep.stdout:
        words.append(ss.stem(word.decode('utf-8').strip('\n')))

    return words


if __name__ == '__main__':
    main()
