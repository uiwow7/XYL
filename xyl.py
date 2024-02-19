import istr, math, sys, os, random, time, datetime, json, threading, copy # unused inputs are for pyeval and pyexec functions in code

keywords = {"print": 1, "include": 1, "pyexec": 1, "if": 1, "while": 1, "for": 2, "else": 0, "function": 2, "return": 1, "not": 1, "true": 0, "false": 0, "call": 2, "run": 0, "pyeval": 1, "class": 2}
#DONE: print, includde, pyexec, /, if, else, function, not, true, false, pyeval
#TODO: return, for (call and run were useless; I'm removing them in favor of implementing classes)
blockKeywords = ["while", "function", "for", "if", "else", "class."]

operators = ["+", "-", "/", "*", "^", "%", "or", "and", "==", ">", "<", "<=", ">=", "=", "::", "+=", "-=", "*=", "/=", "<<", ">>", "&", "|"] 

SUBCOMMANDS = { # {"::": [(expr[0])=thing, (expr[1])={fn: args}]}
    "list": {
        "add": "self.vars[expr[0].val].append(self.exprEval(list(expr[1].values())[0])[0])",
        "remove": "self.vars[expr[0].val].remove(self.exprEval(list(expr[1].values())[0])[0])",
        "item": "rv = self.vars[expr[0].val][list(expr[1].values())[0]]",
        "indexof": "rv = self.vars[expr[0].val].index(list(expr[1].values())[0])",
        "toString": "rv = str(self.vars[expr[0].val])",
        "combinedString": "rv = istr.liststr(self.vars[expr[0].val])"
    },
    "int": {
        "toString": "rv = str(self.vars[expr[0].val])"
    },
    "float": {
        "toString": "rv = str(self.vars[expr[0].val])",
        "round": "rv = round(self.vars[expr[0].val])"
    }
}

ASSIGN_OPS = ["=", "+=", "-=", "*=", "/="]

def tkInList(t, l):
    print("tkinlist", t, l)
    for r in l:
        if type(r) == Token:
            if r.typ == t.typ and r.val == t.val:
                return True
    return False

def tkIndex(t, l):
    for i, r in enumerate(l):
        if type(r) == Token:
            if r.typ == t.typ and r.val == t.val:
                return i
    return False

class Token:
    def __init__(self, typ, val = None):
        self.typ = typ
        self.val = val
    def __repr__(self) -> str:
        return f"({self.typ})" if self.val == None else f"({self.typ}, {self.val})"
#region lexer
class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.cm = istr.filter(text)
        self.tokens = []
        
    def tokenize(self):
        for word in self.cm:
            #print(f"'{word}'", word == "&", word=="|", word == "/")
            if word in keywords.keys() or word in operators:
                self.tokens.append(Token(word))
            elif word == "(":
                self.tokens.append(Token("open-paren"))
            elif word == ")":
                self.tokens.append(Token("close-paren"))
            elif word == "[":
                self.tokens.append(Token("open-bracket"))
            elif word == "]":
                self.tokens.append(Token("close-bracket"))
            elif word == "==":
                self.tokens.append(Token("equals"))
            elif word == "<":
                self.tokens.append(Token("less-than"))
            elif word == ">":
                self.tokens.append(Token("greater-than"))
            elif word[0] == "@":
                self.tokens.append(Token("var", word[1:]))
            elif word[0] == "#":
                self.tokens.append(Token("func", word[1:]))
            elif word == "}":
                self.tokens.append(Token("end"))
            elif word == "::":
                self.tokens.append(Token("from"))
            elif word == ";" or word == ":" or word == "," or word == "!" or word == "{":
                print("SEP TOKEN")
                self.tokens.append(Token("sep"))
            elif word[-1] == "f":
                self.tokens.append(Token("float", word[:-1]))
            else: # interpret as value
                if istr.isNum(word):
                    self.tokens.append(Token("int", word))
                elif word[0] == '"' and word[-1] == '"':
                    self.tokens.append(Token("str", word[1:-1]))
                else:
                    print(f"ERROR: INVALID WORD `{word}`")
                    exit(1)
                    
    def crossreference(self):
        cfStack = []
        for i in range(len(self.tokens)):
            op = self.tokens[i]
            if op.typ == "do" or op.typ == "function" or op.typ == "while" or op.typ == "if":
                cfStack.append(i)
            elif op.typ == "else":
                doip = cfStack.pop()
                if self.tokens[doip].typ == "do":
                    self.tokens[doip].val = i + 1
                    cfStack.append(i)
                else:
                    print("ERROR: `else` can only be preceeded by `do` blocks.")
                    exit(1)
            elif op.typ == "end":
                blockip = cfStack.pop()
                previp = 0
                if self.tokens[blockip].typ == "do":
                    previp = cfStack.pop()
                    if previp.typ == "while":
                        op.val = previp
                    elif previp.typ == "if":
                        self.tokens[doip].val = i
                        op.val = i + 1
                    else:
                        print("ERROR: `do` cannot be preceded by anything other than `while` or `if`.")
                        exit(1)
                elif self.tokens[blockip].typ == "else":
                    self.tokens[blockip].val = i + 1
                    op.val = i + 1
                else:
                    print("ERROR: `}` closing unexpected block")
            
#endregion

#region parser
         
class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens: list[Token] = tokens
        self.tree: dict = {"main": []}
    
    def incrementAfterList(self, expr: list[Token], index: int):
        expr = expr[index:]
        amountToInc = 0
        depth = 0
        for i in expr:
            amountToInc += 1
            if i.typ == "open-bracket":
                depth += 1
            elif i.typ == "close-bracket":
                depth -= 1
                if depth == 0:
                    break
                
        return amountToInc
    
    def parseBlock(self, expr: list[Token], index: int):
        print("PARSING NEW BLOCK")
        tokensList = []
        ati = 0
        depth = 1
        while True:
            index += 1
            ati += 1
            op = expr[index]
            if op.typ in blockKeywords:
                depth += 1
            elif op.typ == "end":
                depth -= 1
                if depth == 0:
                    break
            tokensList.append(op)
            print("blk", ati, index, depth, op, expr[ati:ati+5],"...")
        
        # print("block1", self.parseExpr(tokensList))
        # print("DONE BLOCK", ati)
        print("\nEXPR STARTED FROM PARSEBLOCK\n")
        return {"block": self.parseExpr(tokensList)}, ati
    
    def parseList(self, expr: list[Token], index: int):
        length = 0
        returnList = []
        tokensList = []
        allTokens = []
        print("parsing list", expr)
        while True:
            index += 1
            op = expr[index]
            #print(op, returnList)
            #print(op, expr)
            if op.typ == "sep":
                length += 1
                print("\nEXPR STARTED FROM PARSELIST\n")
                returnList.append(self.parseExpr(tokensList))
                allTokens.extend(tokensList)
                #print("tokens", tokensList)
                tokensList.clear()
                continue
            elif op.typ == "open-bracket":
                rl, tl = self.parseList(expr, index)
                index += self.incrementAfterList(expr, index) - 1
                returnList.append(rl)
                #tokensList.clear()
                continue         
                # print(index, expr, len(tl), len(expr), expr[index + len(tl)*2+1:])
            elif op.typ == "close-bracket":
                length += 1
                print("\nEXPR STARTED FROM PARSELIST\n")
                if len(tokensList) > 0: returnList.append(self.parseExpr(tokensList))
                allTokens.extend(tokensList)
                break
                
            tokensList.append(op)
          
        return Token(f"list", returnList), allTokens
        
    def parseFunctionArgs(self, expr: list[Token], index: int, numArgs: int):
        argsEncountered = 0
        args = []
        tokensList = []
        atc = 0
        while argsEncountered < numArgs:
            index += 1
            atc += 1
            print("parsing args", expr, index)
            print("encountered", argsEncountered, expr[index])
            op = expr[index]
            if op.typ == "sep":
                argsEncountered += 1
                print("tl", tokensList)
                print("\nEXPR STARTED FROM PARSEFUNCTIONARGS\n")
                #print("ptl", self.parseExpr(tokensList))
                args.append(self.parseExpr(tokensList))
                tokensList.clear()
                continue
            elif op.typ == "open-bracket":
                rl, tl = self.parseList(expr, index)
                tokensList.append(rl)
                inca = self.incrementAfterList(expr, index) - 1
                print("inc", inca, expr[index+inca:])
                index += inca 
                atc += inca
                print(index, expr, expr[index])
            if not op.typ == "open-bracket": tokensList.append(op)
            
        print("DONE", args)
        return args, atc
                
            
    def parseExpr(self, expr: list[Token], isMain = False):
        cmds: list[dict|list] = []
        i = -1
        while i + 1 < len(expr):
            i += 1
            op = expr[i]
            print("expr", op, "...", expr[i-5:i+5], "...", i)
            print("AST", cmds)
            if isMain: print(f"\nMAIN EXPR {i}\n")
            if op.typ in keywords.keys(): 
                if keywords[op.typ] == 0:
                    if op.typ in blockKeywords:
                        print("PARSING BLOCK")
                        rd, ati = self.parseBlock(expr, i)
                        print("DONE PARSING", rd)
                        i += ati
                        print("after ati", expr[i:])
                        cmds.append({op.typ: rd})
                    else:
                        cmds.append(op)
                else:
                    print("parsing args")
                    args, atc = self.parseFunctionArgs(expr, i, keywords[op.typ])
                    i += atc
                    print("after atc", expr[i:])
                    if op.typ in blockKeywords:
                        print("THIS IS BLOCK KEYWORD PARSING")
                        rd, ati = self.parseBlock(expr, i)
                        print("BLOCK PARSING END")
                        i += ati
                        print("after block ati", expr[i:], ati)
                        args.append(rd)
                    cmds.append({op.typ: args})
                    print(f"DONE ARGS; {i}, {op}, {expr}, {cmds}")
            elif op.typ in operators:
                nextToken = expr[i+1]
                val = 0
                print("Operator", nextToken, op.typ, cmds)
                if op.typ == "::":
                    laterT = expr[i+2]
                    if nextToken.typ == "func" and laterT.typ == "open-bracket":
                        print("fn", expr[i+2:])
                        args, tl = self.parseList(expr, i+2)
                        cmds.append({op.typ: [cmds.pop(), {nextToken: args}]})
                        i = i + 1 + self.incrementAfterList(expr, i + 2)
                        print("ai", expr[i:])
                        continue
                if nextToken.typ == "open-paren":
                    expr.pop(i+1)
                    tks = []
                    cps = 1
                    print("eeeee", expr[i+1:])
                    for k in range(len(expr[i+1:])):
                        j = expr[i+1:][k]
                        if j.typ == "open-paren":
                            cps += 1
                        if j.typ == "close-paren":
                            cps -= 1
                            if cps == 0:
                                break
                        tks.append(j)
                
                    i += len(tks)
                    #print("nexpr", expr)
                    
                    print(f"\nEXPR STARTED FROM PARSEXPR AT INDEX {i}\n")                            
                    val = {"expr": self.parseExpr(tks)}
                    print('ERROR IS HERE', expr)
                    #i = -1
                elif nextToken.typ == "open-bracket":
                    rl, tl = self.parseList(expr, i+1)
                    i += self.incrementAfterList(expr, i+1)
                    val = rl
                else:
                    expr.pop(i+1)
                    val = nextToken
                    
                cmds.append({op.typ: [cmds.pop(), val]})

            elif op.typ == "open-paren":
                tks = []
                cps = 1
                print(expr)
                for k in range(len(expr[i+1:])):
                    j = expr[i+1:][k]
                    if j.typ == "open-paren":
                        cps += 1
                    if j.typ == "close-paren":
                        cps -= 1
                        if cps == 0:
                            break
                    tks.append(j)
            
                i += len(tks)
                print(f"\nEXPR STARTED FROM PARSEXPR AT INDEX {i}\n")                            
                cmds.append({"expr": self.parseExpr(tks)})

                
            elif op.typ == "str" or op.typ == "int" or op.typ == "float" or op.typ == "var" or op.typ[:4] == "list" or op.typ == "float":
                cmds.append(op)
            
            elif op.typ == "func":
                print("fn", expr[i+2:])
                args, tl = self.parseList(expr, i+1)
                cmds.append({op: args})
                i = i + 2 + self.incrementAfterList(expr, i + 2)
            
            elif op.typ == "open-bracket":
                print("parse list", expr, i)
                rl, tl = self.parseList(expr, i)
                cmds.append(rl)
                i += self.incrementAfterList(expr, i)
                print("expr after", expr[i:])
                                     
            #print('end of loop', op.typ, expr)
            
        print(f"\n{"MAIN" if isMain else ""} EXPR FINISHED\n")  
        return cmds
#endregion

#region module

class Module:
    def __init__(self, text: str, name: str) -> None:
        print(f'IMPORTING MODULE {name}')
        self.text = text
        self.lxr = Lexer(text)
        self.lxr.tokenize()
        self.prs = Parser(self.lxr.tokens)
        self.ast = self.prs.parseExpr(self.lxr.tokens)
        self.intp = Interpreter(self.ast)
        print("ast:", self.ast)
        self.intp.preProcess()
        self.intp.run()
        # self.vars = self.intp.vars
        # self.funcs = self.intp.funcs
        self.includes = self.intp.includes
        self.methods = self.intp.methods
        self.funcs: dict = {}
        self.vars: dict = {}
        for k in self.intp.funcs.keys():
            self.funcs[f"{name}::" + k] = self.intp.funcs[k]
        for k in self.intp.vars.keys():
            self.vars[f"{name}::" + k] = self.intp.vars[k]
            
    

#endregion

#region interpreter
class Interpreter:
    def __init__(self, ast: list[dict|list|Token]) -> None:
        self.ast: list[dict|list|Token] = ast
        self.vars: dict = {}
        self.funcs: dict = {}
        self.includes: dict = {}
        self.methods: dict = SUBCOMMANDS

    def preProcess(self):
        print("PREPROCESSING", self.ast)
        for i in self.ast:
            print(i, type(i))
            if type(i) == dict:
                op = list(i.keys())[0]
                print("op, keys", op, list(i.keys()))
                if op == "function":
                    print("fn", i[op])
                    self.funcs[i[op][0][0].val] = [
                        i[op][2],
                        self.exprEval(i[op][1])
                    ]
                elif op == "include":
                    print("including", i[op][0][0].val)
                    try:
                        with open(f"./libs/{i[op][0][0].val}.xyl", "r") as f:
                            text = f.read()
                    except FileNotFoundError:
                        print(f"ERROR: Invalid Library `{i[op][0][0].val}`. Check your libs directory.")
                    lib = Module(text, i[op][0][0].val)
                    self.includes[i[op][0][0].val] = lib
                    self.vars.update(lib.vars)
                    self.funcs.update(lib.funcs)
                    print("lfs", lib.funcs)
                    
    
    def getMethod(self, parent, child):
        if parent.typ == "var":
            print(self.vars, type(self.vars[parent.val]).__name__)
            if parent.val in self.vars:
                print("ch", child)
                return SUBCOMMANDS[type(self.vars[parent.val]).__name__][list(child.keys())[0].val] # calling type() because variables in the self.vars dictionary are unpacked
            else:
                print("vsdsdfsdf")
        else:
            print("ERROR: Can only get method from variables.")
    
    def operator(self, op: str, _expr, replace: list = [], replacements: list = []):
        expr = copy.deepcopy(_expr)
        print("rr", replace, replacements, expr)
        flag0 = False
        flag1 = False
        if tkInList(expr[0], replace):
            expr[0] = replacements[tkIndex(expr[0], replace)]
            flag0 = True
        if tkInList(expr[1], replace):
            expr[1] = replacements[tkIndex(expr[1], replace)]
            flag1 = True
        if type(expr[0]) == dict:
            expr[0] = self.exprEval(expr[0], replace, replacements)
            flag0 = True
        if type(expr[1]) == dict:
            expr[1] = self.exprEval(expr[1], replace, replacements)
            flag1 = True
        if not flag0:
            try:
                expr[0] = self.exprEval(expr[0], replace, replacements) if not expr[0].val in self.vars or not op in ASSIGN_OPS else expr[0].val
            except AttributeError:
                expr[0] = self.exprEval(expr[0], replace, replacements) if not expr[0] in self.vars or not op in ASSIGN_OPS else expr[0]
        if not flag1:
            try:
                expr[1] = self.exprEval(expr[0], replace, replacements) if not expr[1].val in self.vars or not op in ASSIGN_OPS else expr[1].val
            except AttributeError:
                expr[1] = self.exprEval(expr[0], replace, replacements) if not expr[1] in self.vars or not op in ASSIGN_OPS else expr[1]
        if type(expr[0]) == list:
            expr[0] = self.exprEval(expr[0], replace, replacements)
        if type(expr[1]) == list:
            expr[1] = self.exprEval(expr[1], replace, replacements)
        print("op", op, expr)
        if op == "+":
            return expr[0] + expr[1]
        if op == "-":
            return expr[0] - expr[1]
        if op == "*":
            return expr[0] * expr[1]
        if op == "/":
            return expr[0] / expr[1]
        if op == "^":
            return expr[0] ** expr[1]
        if op == "or":
            return expr[0] or expr[1]
        if op == "and":
            return expr[0] and expr[1]
        if op == "==":
            return expr[0] == expr[1]
        if op == ">":
            return expr[0] > expr[1]
        if op == ">=":
            return expr[0] >= expr[1]
        if op == "<":
            return expr[0] < expr[1]
        if op == "<=":
            return expr[0] <= expr[1]
        if op == "<<":
            return expr[0] << expr[1]
        if op == ">>":
            return expr[0] >> expr[1]
        if op == "&":
            return expr[0] & expr[1]
        if op == "|":
            return expr[0] | expr[1]
        if op == "=":
            lts = []
            print("setting", expr[0], expr[1])
            if type(expr[1]) == list:
                for j in expr[1]:
                    print(j, expr[1])
                    lts.append(self.exprEval(j, replace, replacements))
                print(f"{expr[0]} = {lts}")
                if type(expr[0]) == Token:
                    self.vars[expr[0].val] = lts
                else:
                    self.vars[expr[0]] = lts
                return
            if type(expr[0]) == Token:
                self.vars[expr[0].val] = expr[1]
            else:
                self.vars[expr[0]] = expr[1]
            return
        if op == "+=":
            try:
                self.vars[expr[0].val] += expr[1].val
            except AttributeError:
                self.vars[expr[0]] += expr[1]
            return
        if op == "-=":
            try:
                self.vars[expr[0].val] -= expr[1].val
            except AttributeError:
                self.vars[expr[0]] -= expr[1]
            return
        if op == "*=":
            try:
                self.vars[expr[0].val] *= expr[1].val
            except AttributeError:
                self.vars[expr[0]] *= expr[1]
            return
        if op == "/=":
            try:
                self.vars[expr[0].val] /= expr[1].val
            except AttributeError:
                self.vars[expr[0]] /= expr[1]
            return
        if op == "::":
            rv = False
            print("getmethod", expr)
            exec(self.getMethod(expr[0], expr[1]))
            return rv if rv else None
    
    def exprEval(self, _expr, replace: list = [], replacements: list = []):
        expr = copy.deepcopy(_expr)
        print("rr", replace, replacements)
        print("evaluating", expr)
        if type(expr) == dict:
            op2 = list(expr.keys())[0]
            if op2 == "expr":
                return self.exprEval(expr[op2], replace, replacements)
            elif op2 in operators:
                print("op4")
                return self.operator(op2, expr[op2], replace, replacements)
            elif type(op2) == list:
                if len(op2) == 1:
                    try:
                        if len(op2[0]) == 1:
                            return op2[0][0]
                    except:
                        return op2[0]
            elif type(op2) == Token:
                if tkInList(op2, replace):
                    return replacements[tkIndex(expr[0], op2)]
                elif op2.typ == "func":
                    t = expr[op2].val
                    rv = self.runFunction(op2.val, t)
                    if rv != None: return rv
                    print("VOID VALUE RETURNED")
                    exit(1)
                return op2.val
            elif op2 == "not":
                return not self.exprEval(expr[op2], replace, replacements)
            elif op2 == "pyeval":
                return eval(self.exprEval(expr[op2], replace, replacements))
            else:
                print(f"ERROR: Invalid type. Came from `{op2}`.")
                raise ValueError
        elif type(expr) == list:
            if len(expr) == 1:
                    try:
                        if len(expr[0]) == 1:
                            return self.exprEval(expr[0][0], replace, replacements)
                    except:
                        return self.exprEval(expr[0], replace, replacements)
        elif type(expr) == Token:
            if tkInList(expr, replace):
                return replacements[tkIndex(expr, replace)]
            if expr.typ == "var":
                if not expr.val in self.vars:
                    print("Hopefully this is being used correctly. If it isn't, there will be a KeyError later in execution.")
                    return expr.val
                print("variable detected", self.vars)
                print("rt", self.vars[expr.val])
                return self.vars[expr.val]
            elif expr.typ == "int":
                return int(expr.val)
            elif expr.typ == "float":
                return float(expr.val)
            elif expr.typ == "true":
                return True
            elif expr.typ == "false":
                return False
            elif expr.typ == "list":
                lts = []
                for j in expr.val:
                    lts.append(self.exprEval(j, replace, replacements))
                return lts
            else:
                return expr.val
        elif type(expr) == str or type(expr) == int:
            return expr
        else:
            print(f"ERROR: Invalid typing on expr. Caused by `{expr}`. Type: {type(expr)}")
            raise ValueError
                    
    def runFunction(self, fname: str, args: list):
        print("running function", fname, args, self.funcs[fname])
        fnr = self.funcs[fname]
        args1 = fnr[1]
        nargs = []
        block = fnr[0]["block"]
        for a in args1:
            nargs.append(Token("var", a))
        print("run", nargs, args, block)
        rv = self.run(nargs, args, block, True)
        return rv
    
    def run(self, replace = [], replacements = [], code = False, inFunction = False):
        elseCheck = False
        print("rr", replace, replacements)
        if not code:
            code = self.ast
        print("RUNNING CODE:", code)
        for index, op in enumerate(code):
            if type(op) == dict:
                op2 = list(op.keys())[0]
                print("op2", op2, op2 in keywords)
                if op2 in keywords:
                    if op2 == "print":
                        print("printing", self.exprEval(op[op2], replace, replacements))
                        print(self.exprEval(op[op2], replace, replacements))
                    elif op2 == "pyexec":
                        exec(self.exprEval(op[op2], replace, replacements))
                    elif op2 == "not":
                        print("not", self.exprEval(op[op2], replace, replacements))
                        print("eval", op[op2])
                        op[op2] = not self.exprEval(op[op2], replace, replacements)
                    elif op2 == "pyeval":
                        op[op2] = eval(self.exprEval(op[op2], replace, replacements))
                    elif op2 == "if":
                        if self.exprEval(op[op2][0], replace, replacements):
                            self.run(replace, replacements, op[op2][1]["block"])
                        else:
                            elseCheck = True
                    elif op2 == "while":
                        while True:
                            cond =  self.exprEval(op[op2][0], replace, replacements)
                            print("While", cond, "vars", self.vars, "eval", op[op2][0])
                            self.run(replace, replacements, op[op2][1]["block"])
                            if not cond:
                                break
                    elif op2 == "else": # Because of this implementation, disconnected elses act as comments
                        if elseCheck:
                            self.run(replace, replacements, op[op2]["block"])
                    elif op2 == "return":
                        if inFunction:
                            print(f"returning {op[op2]}")
                            return self.exprEval(op[op2], replace, replacements)
                        else:
                            print("ERROR: Return expression outside of a function.")
                    elif op2 == "function":
                        continue
                    else:
                        print('TODO')
                        exit(1)
                elif type(op2) == Token:
                    if op2.typ == "func":
                        args = self.exprEval(op[op2])
                        self.runFunction(op2.val, args)
                elif op2 in operators:
                    print("op3")
                    execi = self.operator(op2, op[op2], replace, replacements)
                    if execi:
                        exec(execi)
                    # if return is None, the effect has already happened
                if not op2 == "if":
                    elseCheck = False
        return None
                
   
#endregion   
 
program = """
function "add" : [ @n , @n2 ] {
    return ( @n + @n2 ) ;
}

@f = ( #add [ 1 , 2 ] )
"""
     
ex = '@l = [ ]\nprint "a string" ;'
       
lexer = Lexer(program)
lexer.tokenize()
print("tokens 1", lexer.tokens)
parser = Parser(lexer.tokens)
print("MAIN EXPR STARTED")
ast = parser.parseExpr(lexer.tokens, isMain=True)   
print("\nAST", ast, "\n")
interpreter = Interpreter(ast)
interpreter.preProcess()
interpreter.run()
print(interpreter.vars)
# interpreter.run([Token("var", "a")], [10])
# s = parser.parseExpr(lexer.tokens)
# print(s)
print("fns", interpreter.funcs)