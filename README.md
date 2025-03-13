Jack Compiler

A compiler that translates Jack programming language code into virtual machine code.

Overview
This Jack Compiler transforms high-level Jack language programs into virtual machine code that can be executed on the Hack platform. The compiler follows a standard compilation process, including lexical analysis, syntax parsing, and code generation.

Jack Language Grammar
The Jack language is a simple, Java-like programming language with the following grammar:

Program Structure
```
class: 'class' className '{' classVarDec* subroutineDec* '}'
```

### Class Variable Declarations
```
classVarDec: ('static' | 'field') type varName (',' varName)* ';'
type: 'int' | 'char' | 'boolean' | className
```

### Subroutine Declarations
```
subroutineDec: ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody
parameterList: ((type varName) (',' type varName)*)?
subroutineBody: '{' varDec* statements '}'
varDec: 'var' type varName (',' varName)* ';'
```

### Statements
```
statements: statement*
statement: letStatement | ifStatement | whileStatement | doStatement | returnStatement
letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
whileStatement: 'while' '(' expression ')' '{' statements '}'
doStatement: 'do' subroutineCall ';'
returnStatement: 'return' expression? ';'
```

### Expressions
```
expression: term (op term)*
term: integerConstant | stringConstant | keywordConstant | varName | varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
subroutineCall: subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')'
expressionList: (expression (',' expression)*)?
op: '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '='
unaryOp: '-' | '~'
keywordConstant: 'true' | 'false' | 'null' | 'this'
```

## Compilation Process

1. **Tokenization**: The source code is broken down into tokens (lexical elements).
2. **Parsing**: The tokens are analyzed according to the Jack grammar to build a parse tree shortcutted into .XML format for testing.
3. **Code Generation**: The parse tree is traversed to generate VM code.

## Usage

```
python jackanalyzer.py  [input]
```

Where `[input]` can be:
- A `.jack` file: Compiles a single file
- A directory: Compiles all `.jack` files in the directory

## Output

The jackanalyzer outputs .XML textual parse tree for testing and debugging.

The compiler for each input `.jack` file, the compiler produces a corresponding `.vm` file containing the compiled VM code.

## Requirements

- Java Runtime Environment (JRE)

## Example

Input file `Main.jack`:
```
class Main {
   function void main() {
      do Output.printString("Hello, world!");
      do Output.println();
      return;
   }
}
```

Output file `Main.vm`:
```
function Main.main 0
push constant 12
call String.new 1
push constant 72
call String.appendChar 2
...
call Output.printString 1
pop temp 0
call Output.println 0
pop temp 0
push constant 0
return