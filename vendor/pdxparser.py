#!/usr/bin/python

# Copyright (c) 2021 Matthew Edwards
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

"""A simple Paradox Interactive scripting file parser."""

from argparse import ArgumentParser
from dataclasses import dataclass
from enum import IntEnum
import re
from typing import Any, Dict, List, IO, Optional, Tuple

class PdxTokenType(IntEnum):
    """PDX Parser token types."""

    INVALID = -0
    OPEN = 1
    CLOSE = 2
    EQUAL = 3
    ID = 4
    OP = 5
    STRING = 6
    NUMBER = 7
    DATE = 8

@dataclass
class PdxToken:
    """PDX Parser token object."""

    line: int
    col: int
    text: str
    ty: PdxTokenType

class PdxParser:
    """PDX Parser implementation."""

    def __init__(self):
        """Initialize the parser object."""
        self.line_num: int = 1
        self.col_num: int = 0
        self.tokens: List[PdxToken] = []

    def tokenize(self, stream: IO[Any]):
        """
        Tokenize a stream.

        Params:
          stream (IO[Any]): Stream to tokenize.

        """
        WHITESPACE = re.compile(r"^[ \t\r\n]+")
        ID = re.compile(
            r"^[\.\^':]?[a-zA-Z_-][a-zA-Z0-9_-]*([\.\^':][a-zA-Z0-9_-]+)*")
        OP = re.compile(r"^(<|>|<=|>=|==|!=)")
        STRING = re.compile(r'"(?:[^\\]|(?:\\.))*"')
        DATE = re.compile(r"^[0-9]+(\.[0-9]+){2}")
        NUMBER = re.compile(r"^[\+\-]?[0-9]+(\.[0-9]*)?(?!\.)")

        def make_token(line: str, length: int, ty: Optional[PdxTokenType]):
            if ty is not None:
                self.tokens.append(
                    PdxToken(self.line_num, self.col_num, line[:length], ty))
            self.col_num += length
            return line[length:]

        def tokenize_line(line: str):
            while line:
                if line[0] == '{':
                    line = make_token(line, 1, PdxTokenType.OPEN)
                elif line[0] == '}':
                    line = make_token(line, 1, PdxTokenType.CLOSE)
                elif line[0] == '#':
                    line = make_token(line, len(line), None)
                elif line[0] == '=' and (len(line) == 1 or line[1] != '='):
                    line = make_token(line, 1, PdxTokenType.EQUAL)
                else:
                    match = ID.match(line)
                    if match:
                        line = make_token(line, len(match[0]), PdxTokenType.ID)
                        continue

                    match = OP.match(line)
                    if match:
                        line = make_token(line, len(match[0]), PdxTokenType.OP)
                        continue

                    match = STRING.match(line)
                    if match:
                        line = make_token(
                            line, len(match[0]), PdxTokenType.STRING)
                        continue

                    match = DATE.match(line)
                    if match:
                        line = make_token(
                            line, len(match[0]), PdxTokenType.DATE)
                        continue

                    match = NUMBER.match(line)
                    if match:
                        line = make_token(
                            line, len(match[0]), PdxTokenType.NUMBER)
                        continue

                    match = WHITESPACE.match(line)
                    if match:
                        line = make_token(line, len(match[0]), None)
                        continue

                    raise RuntimeError(
                        f"Invalid character at {self.line_num}:"
                        f"{self.col_num}!")

        for line in stream:
            self.col_num = 1
            tokenize_line(line)
            self.line_num += 1

    def has_tokens(self) -> bool:
        """
        Check if there are still tokens left to parse.

        Returns:
          True if there are still tokens left to be parsed.

        """
        return len(self.tokens) > 0

    def next_token(self) -> PdxToken:
        """
        Consumes the next token in the stream.

        Returns:
          Consumed token.

        """
        if not self.tokens:
            raise RuntimeError(f"Expected more tokens")
        token = self.tokens[0]
        self.tokens = self.tokens[1:]
        return token

    def expect(self, *types: PdxTokenType):
        """
        Consume an expected token type from the stream.

        Params:
          token (PdxToken): Token received
          types (List[PdxTokenType]): Token type(s) to expect.

        Returns:
          Consumed token.

        """
        token = self.next_token()
        if token.ty not in types:
            raise RuntimeError(
                f"Unexpected syntax at {token.line}:{token.col}. "
                f"Expected: {types}")
        return token

    def parse_atom(self) -> Any:
        """
        Parse an atom.

        Returns:
          Atom value.

        """
        token = self.tokens[0]
        if token.ty == PdxTokenType.OPEN:
            return self.parse_list()
        elif token.ty in \
            [PdxTokenType.STRING, PdxTokenType.ID, PdxTokenType.DATE]:
            return self.next_token().text
        elif token.ty == PdxTokenType.NUMBER:
            text = self.next_token().text
            if "." in text:
                return float(text)
            return int(text)
        else:
            raise RuntimeError(
                f"Unexpected syntax at {token.line}:{token.col}. Not an atom.")

    def parse_list_item(self) -> Tuple[str, Any]:
        """
        Parse an item from a list.

        Returns:
          Tuple of KV pair.

        """
        key = self.expect(PdxTokenType.ID, PdxTokenType.NUMBER)
        if self.tokens[0].ty not in [PdxTokenType.EQUAL, PdxTokenType.OP]:
            return key.text, None

        op = self.expect(PdxTokenType.EQUAL, PdxTokenType.OP)
        val = self.parse_atom()
        return key.text, [op.text, val]

    def parse_list(self) -> Dict[str, Any]:
        """
        Parse a list.

        Returns:
          PDX list.

        """
        pdx_list = {}
        self.expect(PdxTokenType.OPEN)
        while self.has_tokens() and self.tokens[0].ty != PdxTokenType.CLOSE:
            key, val = self.parse_list_item()
            if key in pdx_list:
                if type(pdx_list[key]) != list:
                    temp_list = [pdx_list[key]]
                    pdx_list[key] = temp_list
                pdx_list[key].append(val)
            else:
                pdx_list[key] = val

        self.expect(PdxTokenType.CLOSE)
        return pdx_list


    def parse(self, stream: IO[Any]):
        """
        Parse a PDX formatted data stream.

        Params:
          stream (IO[Any]): Stream to tokenize.

        Returns:
          Parsed PDX file as a dictionary of KV pairs.

        """
        self.tokenize(stream)
        main = {}
        while self.has_tokens():
            key, val = self.parse_list_item()
            if key in main:
                raise RuntimeError(f"Duplicate top-level item '{key}'")
            main[key] = val
        return main


def pdx_parse(filename: str) -> Dict[str, Any]:
    """
    Open and parse a PDX file.

    Params:
      filename (str): Path to PDX file as a string.

    Returns:
      Parsed PDX file as a dictionary of KV pairs.

    """
    with open(filename, "r") as file:
        return PdxParser().parse(file)


if __name__ == "__main__":
    args_parser = ArgumentParser(
        "A simple Paradox Interactive scripting file parser.")
    args_parser.add_argument("file", help="File to parse.")

    args = args_parser.parse_args()
    if args.file:
        print(pdx_parse(args.file))
