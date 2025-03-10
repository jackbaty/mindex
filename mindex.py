#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mindex 1.0.0 - a miniature index creator

This is a simple program that uses LaTeX to create a small printed index from a
mindex file, a form of tab-separated text file. The details of the file format
and the usage of Mindex are described in the README included with this program.

Mindex uses the MIT license; see the LICENSE file for details.

Usage: mindex FILENAME
"""

import argparse
import os
import subprocess
import tempfile
import sys
import shutil
from string import Template

VERSION = "1.1.0"

PAPER_DIMS = {'X': 8.5, 'Y': 11.0}

DEFAULT_CLOSING = "Automatically generated by Mindex %s on \\today." % VERSION
DEFAULT_GUTTER = "0.75em"
DEFAULT_INDENT = "0.75em"

TMP_FNAME = "mindex"

LATEXSTR = Template(r"""
\documentclass{article}
\usepackage[top=${margin_y}in, bottom=${margin_y}in, right=${margin_x}in, left=${margin_x}in]{geometry}
\usepackage[utf8x]{inputenc}
\usepackage{multicol}
\usepackage[columns=${cols}, indentunit=${indent}, columnsep=${gutter}, font=footnotesize, justific=raggedright]{idxlayout}
\usepackage[sc, osf]{mathpazo}
\usepackage{titlesec}
%\renewcommand{\indexname}{\vskip -0.55in}

\begin{document}
\pagestyle{empty}
\begin{center}\large \textbf{${title}}\end{center}
\begin{theindex}
${content}
\end{theindex}

\vfill
\begin{center}\footnotesize \emph{${closing}}\end{center}
\end{document}
""")


def splash():
    print(("Mindex %s – the automatic miniature index printer" % VERSION))
    print("Copyright 2014, 2016, 2019 Soren Bjornstad. See LICENSE for details.")
    print("")


def getPaperSize(which):
    while True:
        ps = input("%s dimension of the finished index (inches): " % which)
        try:
            ps = float(ps)
        except ValueError:
            print("Please enter a number (decimals are okay).")
        else:
            if ps > PAPER_DIMS[which]:
                print(("I can't print an index larger than the paper "
                       "(%.01f inches wide)!" % PAPER_DIMS[which]))
            elif ps <= 0:
                print("Think you're being smart, huh? "
                      "These are supposed to be *positive* numbers.")
            elif PAPER_DIMS[which] - ps < 1.0:
                print("Please provide at least half an inch of margin to "
                      "ensure the printer prints all of the page.")
            else:
                return ps


def getBasicParams(fname):
    print("I just need a few parameters before we get started.")

    title = input("Title of this index: ")
    xdim = getPaperSize('X')
    ydim = getPaperSize('Y')
    return {'title': title, 'xdim': xdim, 'ydim': ydim, 'fname': fname}


def calcMargins(params):
    x = (PAPER_DIMS['X'] - float(params['xdim'])) / 2
    y = (PAPER_DIMS['Y'] - float(params['ydim'])) / 2
    return x, y


def calcColumns(xdim):
    cols = xdim / 1.5
    cols = int(cols)
    return cols


def readContent(fname):
    data = []
    errors = []
    sortDict = {}
    with open(fname) as f:
        for entry in f:
            # abort if this is a comment or newline
            if entry[0] == "#":
                continue
            if entry == "\n":
                continue

            # process as entry
            entry = entry.split('\t')
            if len(entry) == 3 and entry[2].strip() != "":
                # sort key specified
                sortDict[entry[2].strip()] = entry[0].strip()
                data.append([entry[2].strip(), entry[1].strip()])
            elif (len(entry) == 3 and entry[2].strip() == "") or \
                 (len(entry) == 2):
                # normal
                data.append([entry[0].strip(), entry[1].strip()])
            else:
                # invalid
                errors.append(entry)
                continue

    # the data list is now composed of sort keys; sort by these, then replace
    # the sort keys with the actual content if necessary
    data.sort(key=lambda x: x[0].lower())
    for i in data[:]:
        if i[0] in sortDict:
            i[0] = sortDict[i[0]]

    if errors:
        print("")
        print("The following lines are invalid and were ignored:")
        print("----- BEGIN MINDEX FILE ERRORS -----")
        for i in errors:
            print(i)
        print("----- END MINDEX FILE ERRORS -----")
        input("(press any key to continue)")

    return data


def formatIndex(data):
    index = ""
    for i in data:
        index += "\\item ~%s, %s" % (i[0], i[1])
    return index


def prepLaTeX():
    tdir = tempfile.mkdtemp()
    os.chdir(tdir)
    # we are now in tdir for the rest of the program
    return tdir


def outputLaTeX(params):
    with open("%s.tex" % TMP_FNAME, 'w') as f:
        f.write(LATEXSTR.substitute(params))

    try:
        subprocess.check_output(
            ['pdflatex', '-interaction=nonstopmode', TMP_FNAME],
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print("An error occurred while compiling your index.")
        yn = input("Would you like to see the TeX output (y/n)?")
        if yn.lower()[0] == 'y':
            print("----- BEGIN pdfLaTeX OUTPUT -----")
            print((e.output))
            print("----- END pdfLaTeX OUTPUT -----")
            input("(press any key to continue)")
    else:
        ofile = "%s.pdf" % TMP_FNAME
        if sys.platform.startswith('linux'):
            subprocess.call(["xdg-open", ofile])
        elif sys.platform == "darwin":
            os.system("open %s" % ofile)
        elif sys.platform == "win32":
            os.startfile(ofile)
        else:
            print("Unable to automatically open the output. Please"
                  "browse manually to %s." % ofile)


def clearscreen():
    """Clear the console screen."""

    print("")  # sometimes the display ends up off by a line if you don't do this
    if os.name == "posix":
        os.system('clear')
    elif os.name in ("nt", "dos", "ce"):
        os.system('CLS')
    else:
        print(('\n' * 100))


def modificationLoop(params):
    while True:
        clearscreen()
        print("Mindex Tweaks Menu")
        print("Num\tOption\t\t\tCurrent Value")
        print("---------------------------------------------")
        print(("(1)\tTextblock Width\t\t%.02f in" % params['xdim']))
        print(("(2)\tTextblock Height\t%.02f in"  % params['ydim']))
        print(("(3)\tNumber of Columns\t%i"       % params['cols']))
        print(("(4)\tTitle\t\t\t%s"               % params['title']))
        print(("(5)\tFooter\t\t\t%s"              % params['closing']))
        print(("(6)\tGutter Width\t\t%s"          % params['gutter']))
        print(("(7)\tIndent Width\t\t%s"          % params['indent']))
        print("(0)\tQuit Mindex")
        num = input(">>> ")
        if num == "0":
            return
        elif num == "1":
            params['xdim'] = getPaperSize('X')
            params['margin_x'], params['margin_y'] = calcMargins(params)
        elif num == "2":
            params['ydim'] = getPaperSize('Y')
            params['margin_x'], params['margin_y'] = calcMargins(params)
        elif num == "3":
            ri = input("New number of columns: ")
            try:
                ri = int(ri)
            except ValueError:
                print("Number of columns must be an integer.")
                input("(press any key to continue)")
            else:
                params['cols'] = ri
        elif num == "4":
            params['title'] = input("New title: ")
        elif num == "5":
            params['closing'] = input("New footer: ")
        elif num == "6":
            params['gutter'] = input("New gutter width (include unit): ")
        elif num == "7":
            params['indent'] = input("New indent width (include unit): ")

        print("Rerunning LaTeX...")
        outputLaTeX(params)


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: mindex FILENAME")
        sys.exit(1)
    else:
        filename = sys.argv[1]
        if not os.path.isfile(filename):
            print("Usage: mindex FILENAME")
            print("(The file you specified does not exist.)")
            sys.exit(2)

    splash()
    params = getBasicParams(filename)
    params['margin_x'], params['margin_y'] = calcMargins(params)
    params['cols'] = calcColumns(params['xdim'])
    params['closing'] = DEFAULT_CLOSING
    params['gutter'] = DEFAULT_GUTTER
    params['indent'] = DEFAULT_INDENT

    data = readContent(params['fname'])
    params['content'] = formatIndex(data)

    tdir = prepLaTeX()
    outputLaTeX(params)
    yn = input("Would you like to tweak the output (y/n)? ")
    if yn and yn.lower()[0] == 'y':
        modificationLoop(params)
    shutil.rmtree(tdir)
