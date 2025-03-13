import os

"""
* A tokenizer that generates an xml file output with the tokens from the .jack file
* The tokens are encapsulated with a markup that identifies them
* Governing logic is the Jack Grammar

"""

class Tokenizer:

    def __init__(self, input_file):
        
        self.outputfile = os.path.splitext(input_file)[0] + ".xml"
        self.index = 0
        self.current_token = ""
        self.keywords = ["class","constructor","function","method","field","static","var"
                         ,"int","char","boolean","void","true","false","null","this",
                         "let","do","if","else","while","return"]
        
        self.symbols = ["{","}","(",")","[","]",",",";","+","-","*","/","&","|","<",">","=","~"]
        self.input_file = input_file
        #generate tokes with line numbers
        self.tokens_with_line_numbers = self._generate_tokens_with_line_numbers(input_file=self.input_file)

        self._process_file()


    def _process_file(self):
        
        #open the file
        with open(self.input_file, "r") as f:

            print("SUCCESSFULLY OPENED THE FILE FOR READ.")
            lines = f.readlines()

            #tokens
            self.tokens = self._filter_lines(lines=lines)

            print(f"Successfully generated tokens : {self.tokens}")

            #initialize current token
            if self.tokens and len(self.tokens)>0:
                self.current_token = self.tokens[0]


            
        # write tokens to output file
        #self._write_tokens()

    def _write_tokens(self):

        print("Writing the output file.....")

        #make sure dir exists
        output_dir = os.path.dirname(self.outputfile)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(self.outputfile, "w") as f:

            print("Successfully opened an output file.")
            f.write("<tokens>\n")


            while self.hasMoreTokens():

                token_type = self.tokenType()

                print(f"Current token is : {self.current_token} and is of type : {token_type}")

                if token_type == "KEYWORD":
                    keyword = self.keyword()

                    print(f"Keyword is : {keyword}")
                    xml_markup = self._xml_markup_keyword(token=keyword)
                    f.write(xml_markup + "\n")

                elif token_type =="SYMBOL":
                    symbol = self.symbol()

                    print(f"Symbol is : {symbol}")
                    xml_markup = self._xml_markup_symbol(token=symbol)
                    f.write(xml_markup + "\n")

                elif token_type == "STRING_CONST":
                    string = self.stringVal()
                    xml_markup = self._xml_markup_string_const(token=string)

                    print(f"String is : {string}")
                    f.write(xml_markup + "\n")


                elif token_type == "INT_CONST":
                    integer_cons = self.intVal()
                    xml_markup = self._xml_markup_for_int(token=integer_cons)

                    print(f"Integer Constant is : {integer_cons}")
                    f.write(xml_markup + "\n")


                elif token_type == "IDENTIFIER":
                    identifier = self.identifier()
                    xml_markup = self._xml_markup_identifier(token=identifier)

                    print(f"Identifier is : {identifier}")
                    f.write(xml_markup + "\n")

                    #handle other token types

                self.advance()

            f.write("</tokens>\n")
            


    def _generate_tokens_with_line_numbers(self, input_file:str):
        current_token=""
        tokens =[]
        in_block_comment=False
        in_string = False
        line_number = 1

        with open(input_file, "r") as f:
            
            #read line at a time
            for line in f:
                
                #set char
                i=0
                while i < len(line):
                    
                    char = line[i]

                    if in_block_comment:
                        if char == "*" and i+1 < len(line) and line[i+1]=="/":
                            in_block_comment=False
                            i+=2 # skip the 2 characters

                        else:
                            i+=1

                    elif in_string:
                        if char == '"':
                            current_token+=char

                            #add the token
                            token_with_number = (current_token, line_number)
                            tokens.append(token_with_number)
                            current_token = "" #reset
                            in_string = False
                            

                        else:
                            
                            current_token+=char

                        i+=1

                    else:
   
                        if char == "/" and i+1 < len(line):
                            #inline comment break
                            if line[i+1] == "/":

                                break

                            elif line[i+1] == "*":
                                in_block_comment=True
                                i+=2 #skip /*
                                continue

                        if char.isspace():
                            #space
                            if current_token:
                                token_with_number = (current_token, line_number)
                                tokens.append(token_with_number)

                                current_token = ""

                            i+=1

                        elif char == '"':
                            current_token+=char
                            in_string=True
                            i+=1
                            

                        elif char in self.symbols:
                            if current_token:
                                token_with_number=(current_token, line_number)
                                tokens.append(token_with_number)
                                current_token =""

                            token_with_number = (char, line_number)
                            tokens.append(token_with_number)
                            i+=1

                        elif char == ".":
                            if current_token:
                                token_with_number = (current_token, line_number)
                                tokens.append(token_with_number)
                                current_token=""

                            token_with_number = (char, line_number)
                            tokens.append(token_with_number)

                            i+=1
                            

                        # Handle other characters (keywords, identifiers, integers, etc.)
                        else:
                            current_token += char  # build the current_token
                            i += 1  # move to the next charact


                if current_token and not in_block_comment and not in_string:
                        token_with_number = (current_token, line_number)
                        tokens.append(token_with_number)
                        current_token=""

                #increment line number
                line_number+=1

            print(tokens)

            return tokens

                       
  

    def _filter_lines(self, lines: list) -> list:
        tokens = []  # will store final tokens
        in_block_comment = False  # a flag to track whether parser is inside block comment
        in_string = False  # a flag to track whether parser is inside a string
        current_token = ""  # temporary variable to build up the current token

        for line in lines:
            line = line.strip()  # remove leading/trailing whitespace
            i = 0  # index to iterate through each character

            while i < len(line):
                char = line[i]

                # Handle block comments
                if in_block_comment:
                    if char == "*" and i + 1 < len(line) and line[i + 1] == "/":
                        in_block_comment = False  # end of block comment
                        i += 2  # skip the '*/' characters
                    else:
                        i += 1  # skip characters inside the block comment

                # Handle string literals
                elif in_string:
                    if char == '"':
                        in_string = False  # end of string
                        current_token += char  # include the closing quote
                        tokens.append(current_token)  # add the string token
                        current_token = ""  # reset current_token
                    else:
                        current_token += char  # build the string token
                    i += 1  # move to the next character

                # Handle non-string, non-comment content
                else:
                    # Handle inline comments
                    if char == "/":
                        if i + 1 < len(line):
                            next_char = line[i + 1]
                            if next_char == "/":
                                break  # skip the rest of the line (inline comment)
                            elif next_char == "*":
                                in_block_comment = True  # start of block comment
                                i += 2  # skip the '/*' characters
                                continue


                    # handle foo.bar
                    if char == ".":
                        if current_token:
                            tokens.append(current_token)
                            current_token =""

                        tokens.append(char)
                        i+=1
                        continue

                    # Handle string literals (start of string)
                    if char == '"':
                        in_string = True  # start of string
                        current_token += char  # include the opening quote
                        i += 1  # move to the next character
                        continue

                    # Handle symbols
                    if char in self.symbols:
                        if current_token:  # if there's a current_token, add it first
                            tokens.append(current_token)
                            current_token = ""  # reset current_token
                        tokens.append(char)  # add the symbol as a token
                        i += 1  # move to the next character

                    # Handle whitespace
                    elif char.isspace():
                        if current_token:  # if there's a current_token, add it
                            tokens.append(current_token)
                            current_token = ""  # reset current_token
                        i += 1  # move to the next character

                    # Handle other characters (keywords, identifiers, integers, etc.)
                    else:
                        current_token += char  # build the current_token
                        i += 1  # move to the next character

            # After processing the line, add any remaining current_token
            if current_token and not in_block_comment and not in_string:
                tokens.append(current_token)
                current_token = ""  # reset current_token

            
        

        return tokens
                    


    def _xml_markup_keyword(self, token):
        #markup keyword
        return f"<keyword>{token}</keyword>"
    

    def _xml_markup_identifier(self, token):
        #markup identifier
        return f"<identifier>{token}</identifier>"
    

    def _xml_markup_string_const(self, token):
        #markup string const
        return f"<stringConstant>{token}</stringConstant>"
    

    def _xml_markup_for_int(self, token):
        #markup for int
        return f"<integerConstant>{token}</integerConstant>"
    

    def _xml_markup_symbol(self, token):
        #markup symbol

        if token == "<":
            token = "&lt;"

        elif token == ">":
            token = "&gt;"

        elif token == "&":
            token = "&amp;"

        
        return f"<symbol>{token}</symbol>"

        
            

    def hasMoreTokens(self):
        #is there more tokens?
        return self.index < len(self.tokens)

    def advance(self):

        #next token
        if self.hasMoreTokens():
            self.index+=1

        # advance current token
            if self.index <len(self.tokens):
                self.current_token = self.tokens[self.index]

    def tokenType(self):
        #return the token type
        if self.current_token in self.keywords:
            return "KEYWORD"
        
        elif self.current_token in self.symbols:
            return "SYMBOL"
        
        elif self.current_token.isdigit() and 0<= int(self.current_token)<=32767:
            return "INT_CONST"
        
        elif self.current_token.startswith('"') and self.current_token.endswith('"'):
            return "STRING_CONST"
        
        else:

            return "IDENTIFIER"


    def keyword(self):
        #return keyword
        if self.tokenType() == "KEYWORD":
            return self.current_token
        


    def symbol(self):
        #return symbol
        if self.tokenType() == "SYMBOL":
            return self.current_token
        



    def identifier(self):
        #return identifier
        if self.tokenType() == "IDENTIFIER":
            return self.current_token

    def intVal(self):
        #return identifier
        if self.tokenType() == "INT_CONST":
            return int(self.current_token)
        
        

    def stringVal(self):
        #return string value without the ""
        if self.tokenType() == "STRING_CONST":
            return self.current_token[1:-1]
        



#tokenizer = Tokenizer(input_file=r"C:\Users\LENOVO\Documents\nand_2_tetris_2\nand2tetris\projects\10\ArrayTest\Main.jack")