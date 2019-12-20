#!/usr/bin/env python
# TeX Checker    NDD   21/03/08  (translated from bash/awk to python, 30/08/19)
# Script for performing various checks on TeX files.

try:
    import os,re,sys,math
    import textwrap as tw
except ImportError:
    sys.exit("Need the following modules: os, re, sys, math and textwrap.")

# Colours.
default="\033[0m" ; black="\033[30m" ; red="\033[31m"
green="\033[32m"  ; brown="\033[33m" ; blue="\033[34m"
purple="\033[35m" ; cyan="\033[36m"  ; grey="\033[37m"

usage="tex_checker [-help] file1.tex [file2.tex] ..."

# Regular expression for matching Roman numerals.
romannumeralre=re.compile(r"^[IVXLCDM]*$")


def errstop(message):
    """Report an error message and halt."""
    sys.exit(tw.fill(red+"Error: "+message+default))


def stripcomments(fstr):
    """Get rid of comments and verbatim sections."""
    fstr_new=re.sub(r"^[ \t]*%.*$","",fstr,flags=re.MULTILINE)
    fstr_new=re.sub(r"^(.*[^\\\n])%.*$",r"\1",fstr_new,flags=re.MULTILINE)
    fstr_new=re.sub(r"\\begin\{verbatim\}.*?\\end\{verbatim\}",
                    r"\\begin{verbatim} \\end{verbatim}",fstr_new,
                    flags=re.DOTALL)
    fstr_new=re.sub(r"\\begin\{lstlisting\}.*?\\end\{lstlisting\}",
                    r"\\begin{lstlisting} \\end{lstlisting}",fstr_new,
                    flags=re.DOTALL)
    return fstr_new


def stripeqns(fstr):
    """Get rid of standalone equations."""
    fstr_new=re.sub(r'(\\begin\{(math|equation\*?|displaymath'
                    r'|eqnarray\*?|align)\}|\\[\(\[]).*?(\\\end\{(math'
                    r'|equation\*?|displaymath|eqnarray\*?|align)\}|\\[\]\)])',
                    r"\1 xxx \3",fstr,flags=re.DOTALL)
    return fstr_new


def stripinline(fstr):
    """Get rid of inline equations."""
    fstr_new=re.sub(r"([^\\])\$\$.*?[^\\]\$\$",r"\1$xxx$",fstr,flags=re.DOTALL)
    fstr_new=re.sub(r"([^\\])\$.*?[^\\]\$",r"\1$xxx$",fstr_new,flags=re.DOTALL)
    return fstr_new


def reportissues(x,message):
    """Report issues, giving lines where each issue occurs."""
    if x:
        print(tw.fill(purple+"Possible "+message+":"+default))
        print("\n".join(x)+"\n")


def checkat(fstr):
    """Check for missing \@."""
    x=re.findall(r"^.*\w[A-Z][\)\]']*\.[\)\]']*(?:[ \t~].*)?$",fstr,
                 re.MULTILINE)
    reportissues(x,r'need for "\@"')


def checkdoubledots(fstr):
    """Look for double dots."""
    x=re.findall("^.*(?<!right)\.\..*$",fstr,re.MULTILINE)
    reportissues(x,"double dots")


def checkdoublecapitalisation(fstr):
    """Look for double capitalisation."""
    excludes=("MHz","GHz","THz","MPa","GPa","TPa","MPhys","OKed","OKing",
              "HCl","BSc","MSci")
    y=set(re.findall(r"[\s~]([A-Z][A-Z][a-z][a-z]+?|[A-Z][A-Z][a-rt-z])[\s~]",
                     fstr))
    z=[t for t in y if t not in excludes]
    if z:
        x=re.findall(r"^.*(?:"+r"|".join(z)+r").*$",fstr,re.MULTILINE)
        reportissues(x,"double capitalisation")


def checkmissingcapitalisation(fstr):
    """Check for missing capitalisation."""
    x=re.findall(r"^.*\.[\)\]\}']*[\s~]+[a-z].*$",fstr,re.MULTILINE)
    reportissues(x,"missing capitalisation")


def checkmissingbackslash(fstr):
    """Check for "e.g. XXX"."""
    x=re.findall(r"^.*(?:i\.e\.|e\.g.\|n\.b\.)(?:[ \t~].*)?$",fstr,
                 re.MULTILINE|re.IGNORECASE)
    reportissues(x,r'missing "\ "')
    x=re.findall(r"^.*a\.u\.\s+[a-z].*$",fstr,re.MULTILINE)
    reportissues(x,r'missing "\ "')


def checkinvcommas(fstr):
    """Look for back-to-front inverted commas, etc."""
    x=re.findall(r"^.*[^\\\n]\".*$|^(?:.*[ \t~])?'.*$|^.*\`(?:[ \t~].*)?$",fstr,
                 re.MULTILINE)
    reportissues(x,"erroneous speech marks")


def checkanconsonant(fstr):
    """Look for "an consonant"."""
    x=re.findall(r"^(?:.*[ \t~])?[Aa]n[\s~]+(?:[bcdfgjklmnpqrstvwxyz]"
                 r"|[BCDFGJKLMNPQRSTVWXYZ][a-z]).*$",fstr,re.MULTILINE)
    reportissues(x,r'"an consonant"')


def checkavowel(fstr):
    """Look for "a vowel".  NB, one can have "a unicorn", etc."""
    x=re.findall(r"^(?:.*[ \t~])?a[\s~]+[aei].*$",fstr,
                 re.MULTILINE|re.IGNORECASE)
    reportissues(x,r'"a vowel"')


def checkerthat(fstr):
    """Look for "er that"."""
    excludere=re.compile(r"(?:remember|order|layer|however|compiler|power"
                         r"|parameter|barrier)[\s~]+that",re.IGNORECASE)
    y=re.findall(r"^.*er[\s~]+that[\s~].*$|^(?:.*[ \t~])?less[\s~]"
                 r"+that(?:[ \t~].*)?$",fstr,re.MULTILINE|re.IGNORECASE)
    x=[t for t in y if not excludere.search(t)]
    reportissues(x,r'"...er that"')


def checkspacestop(fstr):
    """Look for " ."."""
    x=re.findall(r"^(?:.*[ \t~])?(?<!\\tt )[\.\,:;\?\!].*$",fstr,re.MULTILINE)
    reportissues(x,"space before punctuation mark")


def checkstopcolon(fstr):
    """Look for ".: "."""
    x=re.findall(r"^.*\.:(?:[ \t~].*)?$",fstr,re.MULTILINE)
    reportissues(x,"need for backslash after colon")


def checklyhyphen(fstr):
    """Look for "ly-"."""
    x=re.findall(r"^.*ly-[a-z].*$",fstr,re.MULTILINE|re.IGNORECASE)
    reportissues(x,"unnecessary hyphen")


def checkneedendash(fstr):
    """Look for e.g. "3-6"."""
    x=re.findall(r"^(?:.*[^\{\d\n][ \t~]*)?\d+[\s~\$]*-[\s~\$]*\d.*$",
                 fstr,re.MULTILINE)
    reportissues(x,"need for an en-dash")


def checkrep(fstr):
    """Check for repetition of of words."""
    excludes=(r"\hline",r"&",r"\\",r"\end{itemize}",r"\end{enumerate}",
              r"\end{description}")
    excludesre=re.compile(r"^\d+,?$|^[A-Z]\.?\\?$")
    lw=""
    x=[]
    for l in fstr.splitlines():
        for iw,w in enumerate(l.split()):
            if w==lw and not w in excludes and not excludesre.search(w):
                if iw==0:
                    x.append("... "+w+"\n"+l)
                else:
                    x.append(l)
            lw=w
    reportissues(x,"repetition of words")


def checkeqref(fstr):
    """Look for e.g. "Eq.\ \ref"."""
    x=re.findall(r"^(?:.*[ \t~])?(?:[eE]qn?s?\.?\\?|[eE]quations?)[\s~]"
                 r"+(?:\\ref|\d).*$",fstr,re.MULTILINE)
    reportissues(x,r'"Eq.\ \ref" (brackets needed)')


def checkeqspace(fstr):
    """Look for e.g. "Eq. "."""
    x=re.findall(r"^$(?:.*[ \t~])?(?:[eE]qn?|[rR]ef|[fF]ig|[sS]ec)s?\.?"
                 r"(?:[ \t~].*)?$",fstr,re.MULTILINE)
    reportissues(x,r'missing "\ "')


def checkwrongabbrev(fstr):
    """Look for e.g. "Sentence.  Eq. "."""
    x=re.findall(r"^.*\.\s+(?:Eqn?|Ref|Fig|Sec)s?\..*$",fstr,
                 re.MULTILINE|re.IGNORECASE)
    reportissues(x,"need to use nonabbreviated form at start of a sentence")


def checkmissabbrev(fstr):
    """Look for e.g. "in Equation"."""
    x=re.findall(r"^.*[A-Z,;:a-z]\s+(?:Equation|Reference|Figure|Section)"
                 r"[\s~]*(?:\(?\\ref|\d).*$",fstr,re.MULTILINE)
    reportissues(x,"need to use abbreviated form in middle of a sentence")


def checkendash(fstr):
    """Look for " --"."""
    x=re.findall(r"^(?:.*[ \t~])?--.*$",fstr,re.MULTILINE)
    reportissues(x,"need to delete space before dash")
    x=re.findall(r"^.*[^\d\n]--(?:[ \t~].*)?$",fstr,re.MULTILINE)
    reportissues(x,"need to delete space after dash")


def checkrefcase(fstr):
    """Look for e.g. "eq."."""
    x=re.findall(r"^(?:.*[ \t~])?(?:eqn?|fig|sec|table|ref)s?\.($:[ \t~].*)?$",
                 fstr,re.MULTILINE)
    reportissues(x,"need to use a capital letter")


def checkminus(fstr):
    """Look for dodgy minus signs."""
    x=re.findall(r"^(?:.*(?:[ \t~]|[^\{\n]\d))?-\d.*$",fstr,re.MULTILINE)
    reportissues(x,"need to use math mode for minus sign")


def checknonascii(fstr):
    """Look for non-ASCII characters."""
    x=re.findall(r"^.*[^\x20-\x7E\x0A\x0D\n].*$",fstr,re.MULTILINE)
    reportissues(x,"non-printable-ASCII character(s)")
    if "\r" in fstr: print(purple+"MS-DOS-style carriage returns.  "
                           "Run dos2unix."+default+"\n")


def checkbib(fstr):
    """Check size of thebibliography."""
    nb=len(re.findall(r"\\bibitem",fstr))
    if nb>0:
        nd=int(math.log(float(nb))/math.log(10.0))+1
        if not re.search(r"\{thebibliography}{\d{"+str(nd)+r"}\}",fstr):
            print(purple+"Possible problem with number of bibitems.")
            print(blue+"Number of bibitems: "+green+str(nb)+default)
            bibmatch=re.search(r"\{thebibliography\}\{\d*\}",fstr)
            if bibmatch:
                print(blue+"File contains     : "+default+bibmatch.group(0)
                      +"\n")
            else:
                print(purple+"thebibliography is missing."+default+"\n")


def checkfoils(fstr):
    """Look for things that shouldn't occur in foils."""
    x=re.findall(r"^.*\\textit.*$",fstr,re.MULTILINE)
    reportissues(x,r'"\textit"')
    x=re.findall(r"^.*\\textsc.*$",fstr,re.MULTILINE)
    reportissues(x,r'"\textsc"')
    x=re.findall(r"^.*\\begin{equation}.*$",fstr,re.MULTILINE)
    reportissues(x,r'"equation"')
    x=re.findall(r"^.*\\footnote{[^~].*$",fstr,re.MULTILINE)
    reportissues(x,r'missing "~"')


def checknotfoils(fstr):
    """Look for things that shouldn't occur in files that aren't foils."""
    x=re.findall(r"^.*\\textsl.*$",fstr,re.MULTILINE)
    reportissues(x,r'"\textsl"')
    x=re.findall(r"^.*\\begin{displaymath}.*$",fstr,re.MULTILINE)
    reportissues(x,r'"displaymath"')
    x=re.findall(r"^.*\\begin{eqnarray\*}.*$",fstr,re.MULTILINE)
    reportissues(x,r'"eqnarray*"')
    x=re.findall(r"^.*\\footnote{~.*$",fstr,re.MULTILINE)
    reportissues(x,r'"\footnote{~"')


def checkwordcite(fstr):
    """Look for " \cite"."""
    x=re.findall(r"^(?:.*[ \t~])?\\cite.*$",fstr,re.MULTILINE)
    reportissues(x,r'" \cite"')


def checksuperscriptcite(fstr):
    """Look for ".\cite"."""
    x=re.findall(r"^.*[^\s~\n]\\cite.*$",fstr,re.MULTILINE)
    reportissues(x,r'".\cite"')


def checkacronyms(fstr):
    """Check whether acronyms are defined.  Exclude country names, etc.,
    and exclude Roman numerals."""
    definedacronyms=("NDD","LA1","4YB","CB3","0HE","UK","USA","EU","UAE","OK",
                     "GNU","AMD","AOL","BAE","BMW","BP","CV","HSBC","IBM",
                     "KFC","CCSD")
    acronyms=set(re.findall(r"\s([A-Z][A-Z\d]+)(?:\\@)?[\s\.,;\.\!\?~']",fstr))
    undefined=[]
    for a in acronyms:
        if a in definedacronyms or romannumeralre.search(a): continue
        if not re.search(r"\("+a+r"(?:\\@|s)?\).*\s"+a
                         +r"(?:\\@)?[\s\.,;\.\!\?~']",fstr,re.DOTALL):
            undefined.append(a)
    if undefined:
        print(purple+"Possible need to define the following acronyms:"+default)
        print(tw.fill(", ".join(undefined))+"\n")


def checkmultipleacronyms(fstr):
    """Check whether acronyms are multiply defined."""
    multiple=[]
    for sec in fstr.split(r"\end{abstract}"):
        acronyms=re.findall(r"\(([A-Z][A-Z\d]+)(?:\\@)?\)",sec)
        for a in set(acronyms):
            if not romannumeralre.search(a) and acronyms.count(a)>1:
                multiple.append(a)
    if multiple:
        print(purple+"Possible multiple definitions of acronyms:"+default)
        print(tw.fill(", ".join(multiple))+"\n")


def writeout(fname,fstr):
    """Write out a tex file."""
    print(tw.fill("Writing to "+fname+"..."))
    try:
        with open(fname,"w") as g:
            g.write(fstr)
    except IOError:
        errstop("Error writing to "+fname+".")
    print("Done.\n")


# Main program starts here.
print("\n"+blue+"TeX Checker")
print("==========="+default+"\n")

foilsre=re.compile(r"\\documentclass.*foils",re.MULTILINE)
apsre=re.compile(r"\\documentclass.*(?:prb\s*[,\]]|achemso)",re.MULTILINE)
natre=re.compile(r"\\documentclass.*nature",re.MULTILINE)

for arg in sys.argv[1:]:
    if arg=="-help" or arg=="--help":
        print(tw.fill(usage))
        sys.exit(0)

    print(tw.fill(blue+"Checking file "+green+arg+default)+".\n")

    # Check the file is a TeX file, then read it.
    if not arg.endswith(".tex"):
        errstop("Need to supply a TeX file as a command-line argument.")
    try:
        with open(arg) as f:
            fstr=f.read()
    except IOError:
        errstop("Cannot read "+arg+".")

    # Get rid of comments and verbatim stuff.
    fstr=stripcomments(fstr)
    # Text only versions.
    fstr_noeqns=stripeqns(fstr)
    fstr_nomath=stripinline(fstr_noeqns)
#   writeout("file_minus_comments.tex",fstr)
#   writeout("file_minus_comments_eqns.tex",fstr_noeqns)
#   writeout("file_minus_comments_math.tex",fstr_nomath)

    # What sort of TeX file do we have (Phys. Rev. B / Nature / Foils)?
    aps=bool(apsre.search(fstr)) ; nat=bool(natre.search(fstr))
    foils=bool(foilsre.search(fstr))

    checknonascii(fstr)
    checkdoubledots(fstr)
    checkat(fstr_noeqns)
    checkdoublecapitalisation(fstr_nomath)
    checkmissingcapitalisation(fstr_noeqns)
    checkmissingbackslash(fstr_noeqns)
    checkinvcommas(fstr)
    checkanconsonant(fstr_nomath)
    checkavowel(fstr_nomath)
    checkerthat(fstr_noeqns)
    checkspacestop(fstr_noeqns)
    checkstopcolon(fstr_noeqns)
    checklyhyphen(fstr_noeqns)
    checkneedendash(fstr_noeqns)
    checkrep(fstr_noeqns)
    checkeqref(fstr_noeqns)
    checkeqspace(fstr_noeqns)
    checkwrongabbrev(fstr_noeqns)
    if not nat: checkmissabbrev(fstr_noeqns)
    checkendash(fstr_nomath)
    checkrefcase(fstr_noeqns)
    checkminus(fstr_nomath)

    checkbib(fstr)
    checkacronyms(fstr_noeqns)
    checkmultipleacronyms(fstr_noeqns)

    # Make checks specific to foils.
    if foils:
        checkfoils(fstr)
    else:
        checknotfoils(fstr)

    # Make checks specific to certain journals.
    if aps or nat:
        checkwordcite(fstr_noeqns)
    else:
        checksuperscriptcite(fstr_noeqns)

print(blue+"Done.\n"+default)
