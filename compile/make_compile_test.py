#!/usr/bin/env python3.4
"""
Write compile_data_test.go
"""

import sys
import ast
import subprocess
import dis

inp = [
    ('''1''', "eval"),
    ('''"hello"''', "eval"),
    ('''a''', "eval"),
    # BinOps - strange operations to defeat constant optimizer!
    ('''"a"+1''', "eval"),
    ('''"a"-1''', "eval"),
    ('''"a"*"b"''', "eval"),
    ('''"a"/1''', "eval"),
    ('''"a"%1''', "eval"),
    ('''"a"**1''', "eval"),
    ('''"a"<<1''', "eval"),
    ('''"a">>1''', "eval"),
    ('''"a"|1''', "eval"),
    ('''"a"^1''', "eval"),
    ('''"a"&1''', "eval"),
    ('''"a"//1''', "eval"),
    ('''a+a''', "eval"),
    ('''"a"*"a"''', "eval"),
    # UnaryOps
    ('''~ "a"''', "eval"),
    ('''not "a"''', "eval"),
    ('''+"a"''', "eval"),
    ('''-"a"''', "eval"),
    # Bool Ops
    ('''1 and 2''', "eval"),
    ('''1 and 2 and 3 and 4''', "eval"),
    ('''1 and 2''', "eval"),
    ('''1 or 2''', "eval"),
    ('''1 or 2 or 3 or 4''', "eval"),
    # With brackets
    ('''"1"+"2"*"3"''', "eval"),
    ('''"1"+("2"*"3")''', "eval"),
    ('''(1+"2")*"3"''', "eval"),
    # If expression
    ('''(a if b else c)+0''', "eval"),
    # Compare
    ('''a == b''', "eval"),
    ('''a != b''', "eval"),
    ('''a < b''', "eval"),
    ('''a <= b''', "eval"),
    ('''a > b''', "eval"),
    ('''a >= b''', "eval"),
    ('''a is b''', "eval"),
    ('''a is not b''', "eval"),
    ('''a in b''', "eval"),
    ('''a not in b''', "eval"),
    ('''(a < b < c)+0''', "eval"),
    ('''(a < b < c < d)+0''', "eval"),
    ('''(a < b < c < d < e)+0''', "eval"),

]

def string(s):
    if isinstance(s, str):
        return '"%s"' % s
    elif isinstance(s, bytes):
        out = '"'
        for b in s:
            out += "\\x%02x" % b
        out += '"'
        return out
    else:
        raise AssertionError("Unknown string %r" % s)

def strings(ss):
    """Dump a list of py strings into go format"""
    return "[]string{"+",".join(string(s) for s in ss)+"}"

def const(x):
    if isinstance(x, str):
        return 'py.String("%s")' % x
    elif isinstance(x, int):
        return 'py.Int(%d)' % x
    elif isinstance(x, float):
        return 'py.Float(%g)' % x
    elif x is None:
        return 'py.None'
    else:
        raise AssertionError("Unknown const %r" % x)

def consts(xs):
    return "[]py.Object{"+",".join(const(x) for x in xs)+"}"
    
def _compile(source, mode):
    """compile source with mode"""
    a = compile(source=source, filename="<string>", mode=mode, dont_inherit=True, optimize=0)
    return a, "\n".join([
        "py.Code{",
	"Argcount: %s," % a.co_argcount,
	"Kwonlyargcount: %s," % a.co_kwonlyargcount,
	"Nlocals: %s," % a.co_nlocals,
	"Stacksize: %s," % a.co_stacksize,
	"Flags: %s," % a.co_flags,
	"Code: %s," % string(a.co_code),
	"Consts: %s," % consts(a.co_consts),
	"Names: %s," % strings(a.co_names),
	"Varnames: %s," % strings(a.co_varnames),
	"Freevars: %s," % strings(a.co_freevars),
	"Cellvars: %s," % strings(a.co_cellvars),
	# "Cell2arg    []byte // Maps cell vars which are arguments".
	"Filename: %s," % string(a.co_filename),
	"Name: %s," % string(a.co_name),
	"Firstlineno: %d," % a.co_firstlineno,
	"Lnotab: %s," % string(a.co_lnotab),
        "}",
        ])

def escape(x):
    """Encode strings with backslashes for python/go"""
    return x.replace('\\', "\\\\").replace('"', r'\"').replace("\n", r'\n').replace("\t", r'\t')

def main():
    """Write compile_data_test.go"""
    path = "compile_data_test.go"
    out = ["""// Test data generated by make_compile_test.py - do not edit

package compile

import (
"github.com/ncw/gpython/py"
)

var compileTestData = []struct {
in   string
mode string // exec, eval or single
out  py.Code
dis string
}{"""]
    for source, mode in inp:
        code, gostring = _compile(source, mode)
        discode = dis.Bytecode(code)
        out.append('{"%s", "%s", %s, "%s"},' % (escape(source), mode, gostring, escape(discode.dis())))
    out.append("}")
    print("Writing %s" % path)
    with open(path, "w") as f:
        f.write("\n".join(out))
        f.write("\n")
    subprocess.check_call(["gofmt", "-w", path])

if __name__ == "__main__":
    main()
