# -*- coding: utf-8 -*-
# Author: oorlo
# Twitter @oorlo
# Dec 2017

import urllib2
import html2text
import re
from random import randint
import sys
import cookielib

firstStrip = 1
try:
    basename = sys.argv[1]
except:
    print "Usage: python vlad.py aaacomics"
    sys.exit()

opener = urllib2.build_opener()
baseurl = "http://" + basename + ".subcultura.es/"

OUTPUT_SUFFIX = "_-_Vlad_El_Rescatador.txt"
HEADER_ALT_TEXT = "Alt text: "
HEADER_AUTHOR_COMM = "Comentarios del autor: "
HEADER_AUTHORS_COMM = "Comentarios de los autores: "
HEADER_TITLE = ""
HEADER_COMMENTS = "Comentarios de los usuarios: "
HEADER_LIKES = "Me gusta: "
HEADER_TITLE = ""
TAG_GUESTCOMMENT = " (usuario no registrado)"
TAG_MISSINGSTRIP = "Esta tira no existe! "
TAG_GUARRERIDA = "Tira para +18, no me dejan ver estas cosas!"
TAG_NOCOMMENTS = "No hay comentarios en esta tira"
TAG_LAST_STRIP = "Ultima tira: "
SEPARATOR_COMMENT = "\n"
SEPARATOR_STRIP = "\n\n" + 80*"-" + "\n\n"
SEPARATOR_HEADER = "\n\n" + 80*"~" + "\n" + 80*"~" + "\n\n"
ORDER_RECENTFIRST = 0
ORDER_OLDESTFIRST = 1
WARNING_MISSINGSTRIP = "Esta tira no existe!"
RECAP_MISSINGSTRINGS = "Algunas tiras han fallado! Si de verdad existen, avisa a @oorlo. Perdon!"

FLUFFS = ["Empalagando", "Empanando", "Empatando", "Empacando", "Embalando", "Apilando", "Compilando", "Empachando", "Emplatando", "Encalando", "Escalando"]
URL_REGEX = re.compile(r"""(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>\[\]]+|\(([^\s()<>\[\]]+|(\([^\s()<>\[\]]+\)))*\))+(?:\(([^\s()<>\[\]]+|(\([^\s()<>\[\]]+\)))*\)|[^\s`!(){};:'".,<>?\[\]]))""")
# ^^^ I to-hotally wrote that regex myself
REDBUTTON = "<div align=\"center\"><br><object classid=\"clsid:D27CDB6E-AE6D-11cf-96B8-444553540000\" codebase=\"http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=4,0,2,0\" width=\"50\" height=\"50\"><param name=movie value=\"http://subcultura.es/flashfiles/rimshot.swf\"><param name=quality value=high><embed src=\"http://subcultura.es/flashfiles/rimshot.swf\" quality=high pluginspage=\"http://www.macromedia.com/shockwave/download/index.cgi?P1_Prod_Version=ShockwaveFlash\" type=\"application/x-shockwave-flash\" width=\"50\" height=\"50\"></embed></object>"
MINIREDBUTTON = "<object classid=\"clsid:D27CDB6E-AE6D-11cf-96B8-444553540000\" codebase=\"http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=4,0,2,0\" width=\"13\" height=\"13\"><param name=movie value=\"http://subcultura.es/flashfiles/rimshot.swf\"><param name=quality value=high><embed src=\"http://subcultura.es/flashfiles/rimshot.swf\" quality=high pluginspage=\"http://www.macromedia.com/shockwave/download/index.cgi?P1_Prod_Version=ShockwaveFlash\" type=\"application/x-shockwave-flash\" width=\"13\" height=\"13\"></embed></object>"
def getFluff():
    # World of Goo's loading screen was iconic
    return FLUFFS[ randint(0, len(FLUFFS)-1) ]

def nicify(myString):
    # Removes html escaped characters "<>&', adds the redbuttons
    myString = myString.replace("&quot;", "\"").replace("&lt;", "<").replace("&gt;", ">")
    myString = myString.replace("&amp;", "&").replace("&#39;", "'")
    return myString.replace(REDBUTTON, "[redbutton]").replace(MINIREDBUTTON, "[miniredbutton]")

def standardizeUrl(m):
    # Saves your butt if you try to check https://es.wikipedia.org/wiki/Ñu_(desambiguación)
    return urllib2.quote(m.group(0), safe="%/:=&?~#+!$,;'@()*[]")
    
def sanitizeUrls(text):
    # Applies sanitizeUrls to all urls in an entire block of text
    return URL_REGEX.sub(standardizeUrl, text)
    
def extractAuthorComments(text):
    # takes the block that main thinks contains the author's comments
    # extracts the title of the strip, and the comments of all authors
    title = nicify(re.search('<h2>(.*)</h2>', text).group(1))
    authors = re.findall('<div class=\"avatar\">(.*?)<div class=\"clear\">', text, re.DOTALL)
    nAuthors = len(authors)
    
    if nAuthors == 1:
        prettyText = HEADER_AUTHOR_COMM + "\n"
    else:
        prettyText = HEADER_AUTHORS_COMM + "\n"
        
    for author in authors:
        authorname = re.search('^.*?Avatar.*?Perfil.*?class=\"usuario\">(.*?)</a>', author, re.DOTALL).group(1)
        authorcomment = re.search('&mdash; (.*)</div>', author, re.DOTALL).group(1)
        #I'm so sorry about this:
        authorcomment = authorcomment.encode("utf-8") # now it's a string, for use with standardizeUrl
        authorcomment = sanitizeUrls(authorcomment)
        authorcomment = html2text.html2text(authorcomment.decode("utf-8")) # ...and back to unicode, or html2text dies
        
        prettyText += authorname + "\n" + authorcomment + "\n\n"
        
    return title, prettyText
    
        
        
def processComments(comments, order):
    # takes the array of blocks that main thinks contains each user comment
    # extracts the title of the strip, and the comments of all authors
    niceoutput = HEADER_COMMENTS + "\n\n"
    n = len(comments)
    if order == ORDER_RECENTFIRST: # like they showed up on the web
        myRange = range(n)
    else: # chronological order
        myRange = range(n-1, -1, -1)
        
    def isNotLast(i):
        if order == ORDER_RECENTFIRST:
            return i < n-1
        else:
            return i > 0
    
    for i in myRange:
        comm = comments[i]
        username = re.search("<a href.*?title=\"(.*?)\"", comm)
        if username is None:
            username = re.search("<strong>(.*?)</strong>", comm).group(1) + TAG_GUESTCOMMENT
        else:
            username = username.group(1)
        date = re.search("dijo <span title=\"(.*?)\"", comm).group(1)
        
        # we have to repeat the unicode then string then unicode shenanigans
        content = re.search("<div id=\"comentario_interno_[0-9]*\">(.*?)</li>", comm, re.DOTALL).group(1)
        content = nicify(content)
        content = content.encode("utf-8") # now it's a string, for use with standardizeUrl
        content = sanitizeUrls(content)
        content = html2text.html2text(content.decode("utf-8")) # ...and back to unicode, or html2text dies
        full_comment = username + ", " + date + ":\n" + content 
        if isNotLast(i):
            full_comment += SEPARATOR_COMMENT
        niceoutput += full_comment
    if n == 0:
        niceoutput += TAG_NOCOMMENTS
    return niceoutput
    
def getHeaderInfo(target):
    # Go to the front page, take the name and the description for the comic.
    # I guess one could also grab tags, reviews, fans, etc from here
    # But I'm going to pretend I didn't think of that unless somebody asks.
    done = False
    htmltext = target.readline().strip()

    counter = 0
    while not done:
        if htmltext.startswith("<title>"):
            header_name = nicify(htmltext[7:-8])
        elif htmltext.startswith("<meta name=\"description\""):
            
            while "\" />" not in htmltext:
                htmltext += target.readline()
            lastquote = htmltext.rfind("\"")
            header_description = nicify(htmltext[34:lastquote])
            return header_name, header_description
            
        htmltext = target.readline().strip()
        counter += 1
        if counter > 1000:
            print "Something went wrong reading front page..."
            sys.exit()
            
def getLastStrip(baseurl):
    # We go to the archive, and assume the page closest to the top is the last one.
    # "But this is broken, I reordered my comic and the last strip is not actually the last!"
    # Counterpoint: you're a weirdo, please leave me alone.
    archiveHtml = opener.open(baseurl + "archivo").read()
    return int(re.search(".*?<li><a href=\"../tira/(.*?)\">", archiveHtml).group(1))


def pretendToBeAnAdult(baseurl):
    # add the relevant cookie to see +18 content. Also draw a moustache with sharpie. 
    # My name is Vladcent Adultman. I went to stock market today. I did a business.
    opener.addheaders.append(('Cookie', 'Maria=0%2C+1%2C+1%2C+2%2C+3%2C+5%2C+8%2C+13%2C+21%2C+34%2C+55%2C+89'))
     

    
pretendToBeAnAdult(baseurl)
target = opener.open(baseurl)
text_file = open(basename + OUTPUT_SUFFIX, "w")        
    
header_name, header_description = getHeaderInfo(target)    
text_file.write( header_name + "\n\n" + header_description + SEPARATOR_HEADER )
lastStrip = getLastStrip(baseurl)
print TAG_LAST_STRIP + str(lastStrip)

missing = []

for stripno in range(firstStrip, lastStrip+1):
    print getFluff() + " tira " + str(stripno) + "..."
    address = baseurl + "tira/" + str(stripno)
    target = opener.open(address)
    
    if target.geturl().startswith(baseurl + "comprueba_mayoria_edad/"):
        print "I can't access +18 comics until 2035 :("
        text_file.write(TAG_GUARRERIDA)
        # sys.exit()
    
    if target.geturl() <> address: # passed age check but strip still not there
        text_file.write(TAG_MISSINGSTRIP + ": " + address + SEPARATOR_STRIP)
        missing.append(stripno)
        print WARNING_MISSINGSTRIP
        
        
    else:
        output_date = None
        output_alt_text = None
        for line in target:
            htmltext = line.decode("utf-8").strip()
            
            if htmltext.startswith("<a href=\"/tira/"):
                alt = re.search('title="(.*)"', htmltext).group(1)
                if alt != "Dan coloreado": # Good old Dan. Ignore him.
                    output_alt_text = HEADER_ALT_TEXT + alt
            
            if htmltext == "<div class=\"widget\" id=\"comentarios_autores\">":
                text = "".decode("utf-8")
                htmltext = target.readline().strip().decode("utf-8")
                # while not htmltext.startswith("</div></div>"):
                    # text += htmltext
                    # htmltext = target.readline().strip().decode("utf-8")
                while not htmltext.startswith("<div class=\"avatar\">"):
                    # not yet comment, but we need this for the title
                    text += htmltext
                    htmltext = target.readline().strip().decode("utf-8")
                # we've started the first comment!
                areAuthCommsDone = False
                text += htmltext
                while not areAuthCommsDone: # maybe there's more than one author writing
                    htmltext = target.readline().decode("utf-8").strip()
                    text += htmltext
                    if htmltext.startswith("<div class=\"clear\"></div>"):
                        #we're at the end of a comment, or the block. Which one?
                        htmltext = target.readline().decode("utf-8")
                        while not htmltext.strip():
                            # skip blank lines
                            htmltext = target.readline().decode("utf-8")
                        if "widget" in htmltext:
                            # it's another, lamer widget! We're done
                            areAuthCommsDone = True
                        elif "navegador_select" in htmltext:
                            # I guess this is a different type of widget?
                            # Thanks @fjfuente for catching this!
                            areAuthCommsDone = True
                        else:
                            # a new author comment, start over
                            text += htmltext
                output_title, output_authorcomments = extractAuthorComments(text)
                
            if htmltext == "<ol class=\"lista-1\">":
                # separate in comments!
                comments = []
                htmltext = target.readline() + "\n"
                # skip lines until next meaningful thing
                while not htmltext.strip():
                    htmltext = target.readline().strip()
                while not htmltext.strip().startswith("</ol>"):
                    onecomment = ""
                    while not htmltext.startswith("<li id=\"comentario"):
                        htmltext = target.readline().strip() + "\n"
                    htmltext = target.readline().decode("utf-8").strip() + "\n"
                    while not htmltext.startswith("</li>"):
                        onecomment += htmltext
                        htmltext = target.readline().decode("utf-8").strip() + "\n"
                    onecomment += htmltext
                    comments.append(onecomment)
                    # skip blank lines until next comment/end
                    htmltext = target.readline().strip()
                    while not htmltext:
                        htmltext = target.readline().strip()
                    htmltext = htmltext.strip()
                    
                # we have all comments now
                output_comments = processComments(comments, ORDER_OLDESTFIRST)
                
            if htmltext.startswith("<p>Publicada el"):
                output_date = htmltext[3:-5] # this may be missing though
                
            if htmltext.startswith("<div class=\"boton_like_flecha_texto\">"):
                likes = target.readline().strip()
                output_likes = likes[6:-7]
                    
        header = output_title + "\n"
        if output_date is not None:
            header += output_date + "\n"
        if output_alt_text is not None:
            header += output_alt_text + "\n"
        header += HEADER_LIKES + output_likes + "\n"
        header += "\n"
        
        toWrite = (header + output_authorcomments + output_comments).encode("utf-8")
        if stripno < lastStrip - 1:
            toWrite += SEPARATOR_STRIP
        text_file.write(toWrite)
    
text_file.close()
if len(missing) > 0:
    print RECAP_MISSINGSTRINGS
    print missing
