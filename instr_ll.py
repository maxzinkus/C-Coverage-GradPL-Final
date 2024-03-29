#!/usr/bin/python3

""" 
Max Zinkus
CSC 530
Evaluating traditional code coverage metrics by
tracking code progress over a CFG
"""

F_INSTR_CALL = "  call void @__f_transition(i8* getelementptr inbounds (["
F_INSTR_MID = " x i8]* @."
F_INSTR_TAIL = "str, i32 0, i32 0))"
BB_INSTR_CALL = "  call void @__bb_transition(i64 "
CVG_INIT_CALL = "  call void @__coverage_init()"
CVG_END_CALL = "  call void @__coverage_end()"

F_INSTR_DECLARE = "\ndeclare void @__f_transition(i8*)\n"
BB_INSTR_DECLARE = "\ndeclare void @__bb_transition(i64)\n"
CVG_INIT_DECLARE = "\ndeclare void @__coverage_init()\n"
CVG_END_DECLARE = "\ndeclare void @__coverage_end()\n"

def read_file(fname):
    """ file : str -> [line : str] """
    with open(fname, 'r') as f:
        d = f.readlines()
    return [l.rstrip() for l in d]

def name_from_def(d):
    """ line : str -> function name : str """
    return d[d.index('@')+1:d.index('(')]

def next_close(lines, d):
    """ [line : str] -> line -> index of next '}' : int """
    i = lines.index(d)
    consider = lines[i:]
    close = list(filter(lambda line: line.startswith("}"), consider))[0]
    return i + consider.index(close) + 1

def func_split(lines):
    """ [line : str] -> {name : str :: [line : str]} """
    defs = list(filter(lambda line: line.startswith("define") and not '.' in line, lines))

    funcs = {}
    after = {}
    names = []
    for d in defs:
        name = name_from_def(d)
        if not names:
            pre = lines[:lines.index(d)]
        if defs.index(d)+1 < len(defs):
            after[name] = lines[next_close(lines, d):lines.index(defs[defs.index(d)+1])]
        else:
            after[name] = lines[next_close(lines, d):]
        names.append(name)
        funcs[name] = lines[lines.index(d):next_close(lines, d)]

    return names, pre, funcs, after

def instrument_function(func, lines):
    """ [line : str] -> [line : str] """
    appends = []
    lines.insert(1, F_INSTR_CALL + str(len(func)+1) + F_INSTR_MID + func + F_INSTR_TAIL)
    if func == 'main':
        lines.insert(1, CVG_INIT_CALL)
    for i in range(len(lines)):
        if "; <label>" in lines[i]:
            l = lines[i][lines[i].index('<label>:')+len('<label>:'):lines[i].rindex(';')].strip()
            j = i
            while "phi" in lines[j+1]:
                j += 1
            appends.append((j+1, l))
    while appends:
        i,l = appends.pop()
        lines.insert(i, BB_INSTR_CALL + l + ")")
    if func == 'main':
        lines.insert(-2, CVG_END_CALL)
    return lines

def get_f_name(name):
    return "@." + name + "str = private unnamed_addr constant [" + (
            str(len(name)+1) + " x i8] c\"" + name + "\\00\", align 1")

def build_cfg(lines):
    """ lines -> list of (src, targ) pairs """
    edges = set()
    for line in lines:
        if line.startswith("; <label>:"):
            if "preds" in line:
                lbl = line[line.index('<label>:')+len('<label>:'):line.rindex(';')].strip()
                preds = line[line.rindex('=')+1:].replace('%','').split(', ')
                for pred in preds:
                    edges.add((int(pred.strip()), int(lbl)))
            else:
                raise Exception("Label without predecessors!\n%s" % line)
    return list(edges)

def cfg_pack(cfgs):
    """ CFG encoding
        num funcs : 1
        len(func name) : 1
        func name : ?
        num edges : 1
        src : 4
        dest : 4 (for each block)
                 (for each function)
    """
    s = bytearray()
    s += int.to_bytes(len(cfgs), 1, 'little')
    for cfg in cfgs:
        s += int.to_bytes(len(cfg[0]), 1, 'little')
        s += bytes(cfg[0]+'\0', "ascii")
        s += int.to_bytes(len(cfg[1]), 1, 'little')
        for src,dest in cfg[1]:
            s += int.to_bytes(src, 4, 'little')
            s += int.to_bytes(dest, 4, 'little')
    return bytes(s)

if __name__ == '__main__':
    from sys import argv, stderr, exit
    if len(argv) > 3:
        lines = read_file(argv[1])
        names, pre, funcs, after = func_split(lines)
        with open(argv[2], 'w') as outf:
            outf.write('\n'.join(pre)+'\n')
            outf.write(BB_INSTR_DECLARE+'\n')
            outf.write(F_INSTR_DECLARE+'\n')
            outf.write(CVG_INIT_DECLARE+'\n')
            outf.write(CVG_END_DECLARE+'\n')
            for k in names:
                outf.write(get_f_name(k)+'\n')
            for k in names:
                funcs[k] = instrument_function(k, funcs[k])
                outf.write('\n'.join(funcs[k])+'\n')
                outf.write('\n'.join(after[k])+'\n')
        cfgs = []
        for k in names:
            cfgs.append((k, build_cfg(funcs[k])))
        with open(argv[3], 'wb') as cfgf:
            cfgf.write(cfg_pack(cfgs))
    else:
        print("Usage: python3 instr_ll.py infile outfile cfg_outfile", file=stderr)
        exit(1)
