from codecs import escape_decode

def removecomments(s: str):
    lines = s.splitlines()
    endt = []
    for l in lines:
        endt.append(l.split("//")[0])
    return liststr(endt, end="\n")
def liststr(l:list, end=""):
    s= ""
    for i in l:
        print(i)
        s+=str(i)+str(end)
        print(s)
    return s

def find_col(line,coln):
    col = coln
    try:
        char = line[col]
    except:
        return -1
    while char.isspace() and col < len(line):
        col += 1
        try:
            char = line[col]
        except IndexError:
            return -1 # string is empty or ends with whitespace
    return col

def find_col_end(line,coln):
    col = coln
    char = line[col]
    while not char.isspace() and col < len(line):
        col += 1
        try:
            char = line[col-1]
            if char == "'" or char == '"':
                ochar = char
                s = ""
                s += char
                col += 1
                char = line[col]
                while char != ochar and col < len(line):
                    col += 1
                    char = line[col]
                    s += char
                col += 1
                return col
        except IndexError:
            return -1 # should be unreachable
    return col

def filter(cm: str):
    print("filtering", "'", cm, "'")
    args = []
    loc = 0
    endloc = 0
    while endloc != -1 and loc != -1:
        loc = find_col(cm,endloc)
        endloc = find_col_end(cm,loc)
        cmd = cm[loc:endloc].replace("\\", "BACKSLASH_PLACEHOLDER")
        cmd = cmd.strip()
        cmd = str(escape_decode(cmd.replace("BACKSLASH_PLACEHOLDER", "\\"))[0], "utf-8")
        args.append(cmd)
    return args[:-1]

def isNum(check: str):
    for i in check:
        try:
            x=int(i)
        except:
            return False
        
    return True

def isFloat(check: str):
    for i in check:
        try:
            i = float(i)
        except:
            return False
        
    return True
#################################################################################################################################################################################################################