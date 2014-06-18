# -*- coding: utf-8  -*-
'''
    Copyright (C) 2014  se4598

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
'''
typehint for PyDev see: http://pydev.org/manual_adv_type_hints.html
'''

import pywikibot
from pywikibot import pagegenerators
import re

class pageTreeSupplier:
    class workOnPageException(Exception):
        pass
    
    #matches namespace-id, optional prefix, optional options
    re_instructions = re.compile(r"^@Efen[Bb]ot@ (?P<ns>[\d]*)(?P<prefix> [\S]*|)(?: \| (?P<options>.*?)|)\s*$", re.MULTILINE)
    re_option_redirects = re.compile(r"redirects=([\d])")
    re_option_nesting = re.compile(r"nesting=([\d]+)")
    re_option_stripprefix = re.compile(r"stripprefix=([\d])")
    re_option_targets = re.compile(r"targets=([\d]+)")
    re_modulepage_head = re.compile(r"[\s\S]*\n-- BOT-START[ \r]*$", re.MULTILINE)
    
    def run(self, confirmEdit = True, sandbox = False):
        self.confirmEdit = confirmEdit
        self.site = pywikibot.Site('de', 'wikipedia');
        self.sandbox = sandbox
        
        liste = self.selectWorkOn()
        for page in liste:
            try:
                self.workOnPage(page)
            except self.workOnPageException as e:
                pywikibot.output("Exception for page "+page.title()+"\n"+str(type(e))+":"+str(e)+"\n")
    
    def selectWorkOn(self):
        ':rtype list'
        liste = list()
        if self.sandbox:
            liste.append(pywikibot.Page(self.site, "Benutzer:Se4598/test2", 2))
            return liste
        gen = pagegenerators.PrefixingPageGenerator("Modul:PageTree/", None, True, site=self.site)
        #: :type page: pywikibot.Page
        for page in gen:
            if page.title().endswith("/bot"):
                liste.append(page)
        return liste
    pass

    def workOnPage(self, page):
        ':param Page page:'
        pywikibot.output("working on "+page.title());
        #: :type text: unicode
        text = page.get()
        'Get instructions for bot'
        #: :type match: re.MatchObject
        match = self.re_instructions.search(text)
        if match:
            ns = match.group('ns')
            prefix = match.group('prefix') 
            options = match.group('options')
            if options == None:
                options = ""
            head = self.re_modulepage_head.search(text)
            
            #validate ns and head    
            if not ns.isdigit(): #shouldn't happing b/c regexp match on [\d]*
                raise self.workOnPageException("ERROR: namespace id is not a non-negative integer")
            ns = int(ns)
            
            if head == None:
                raise self.workOnPageException("ERROR: page doesn't have a BOT-START-mark")
            wikitext_head = head.group(0)
            wikitext_head = wikitext_head.replace("@Efenbot@","@EfenBot@") ### MIGRATION --- remove after running
            wikitext_body = self.generatePageTree(nsID=ns, prefix=prefix, optionsString=options)
            
            wikitext = wikitext_head + "\n" + wikitext_body
            comment = u"Bot: Liste aktualisiert"
            self.savePage(page, wikitext, comment)
        
        else:
            pywikibot.output("no instructions for us found");
            return
        
        
    def savePage(self, page, content, comment):
        ':param Page page:'
        if self.confirmEdit:
            pywikibot.output(u">>> \03{lightpurple}%s\03{default} <<<"
                             % page.title())
            # show what was changed
            pywikibot.output('Diffing old and new pagetext...:')
            pywikibot.showDiff(page.text, content)
            pywikibot.output(u'Comment: %s' % comment)
            #pywikibot.output(u'Page: %s' %page.title(asLink=True))
            while True:
                choice = pywikibot.inputChoice(
                u'Do you want to accept these changes?',
                ['Yes', 'No', 'Show all'], ['y', 'N', 'a'], 'N')
                choice.lower() # make choice lowercase
                
                if choice == 'y':
                    break #proceed with save
                elif choice == 'a':
                    pywikibot.output(u'')
                    pywikibot.showDiff('', content)
                    #stay in loop
                else: # n or everything else
                    return False #exit function without save
        page.text = content
        page.save(comment=comment, minor=False)
        
    class Options(object):
        pass # just to randomly set options here
    
    def readOptions(self, optionsString = ""):
        option = pageTreeSupplier.Options()
        option.gen_redirects = True
        option.nesting = None
        option.stripprefix = False
        option.add_prefix = ""
        
        'redirects=([\d])'
        redirects = self.re_option_redirects.search(optionsString)
        if redirects == None:
            redirects = '1'
        else:
            redirects = redirects.group(1)
            
        #Convert redirects
        option.gen_redirects = True
        if redirects == '0':
            option.gen_redirects = False
        elif redirects == '1':
            option.gen_redirects = True
        elif redirects == '2':
            option.gen_redirects = 'only'
        else:
            raise self.workOnPageException('ERROR: invalid option for "redirects"')
            
        'nesting=([\d]+)'
        nesting = self.re_option_nesting.search(optionsString)
        if nesting != None:
            nesting = nesting.group(1)
            if not nesting.isdigit(): #shouldn't happing b/c regexp match on [\d]+
                raise self.workOnPageException("ERROR: nesting is not a non-negative integer")
            option.nesting = int(nesting)
        
        
        'stripprefix=([\d])'
        stripprefix = self.re_option_stripprefix.search(optionsString)
        if stripprefix == None:
            stripprefix = '0'
        else:
            stripprefix = stripprefix.group(1)
        
        #Convert stripprefix
        if stripprefix == '0':
            option.stripprefix = False
        elif stripprefix == '1':
            option.stripprefix = True
        elif stripprefix == '2':
            #for PerfektesChaos: if stripped, must start with slash
            option.stripprefix = True
            option.add_prefix = '/'
        else:
            raise self.workOnPageException('ERROR: invalid option for "stripprefix"')
        
        'targets=([\d]+)'
        targets = self.re_option_targets.search(optionsString)
        if targets == None:
            targets = '0'
        else:
            targets = targets.group(1)
            
        if targets == '0':
            option.targets = False;
        elif targets == '1':
            option.targets = True
        else:
            raise self.workOnPageException('ERROR: invalid option for "targets"')
        
        return option

    def generatePageTree(self, nsID, prefix = "", optionsString = ""):
        prefix = prefix.strip()
        
        option = self.readOptions(optionsString)
        option.prefix = prefix
        
        if option.prefix == "":
            generator = pagegenerators.AllpagesPageGenerator(site=self.site, namespace=nsID, includeredirects=option.gen_redirects)
        else:
            generator = pagegenerators.PrefixingPageGenerator(site=self.site, prefix=option.prefix, namespace=nsID, includeredirects=option.gen_redirects)
            
        
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        redirectpages = dict() # to fill if "targets=1"
        pages = []
        
        if option.targets:
            if option.prefix == "":
                genRedirect = pagegenerators.AllpagesPageGenerator(site=self.site, namespace=nsID, includeredirects='only')
            else:
                genRedirect = pagegenerators.PrefixingPageGenerator(site=self.site, prefix=option.prefix, namespace=nsID, includeredirects='only')
            #: :type page: pywikibot.Page
            for page in genRedirect:
                pywikibot.output('Getting target for: '+self.getTitle(page, option));
                targetPage = page.getRedirectTarget() #could throw IsNotRedirectPage but we're only querying redirects. BUT race-conditions...
                redirectpages[self.getTitle(page, option)] = self.getTitle(targetPage, option) 
                
        #: :type page: pywikibot.Page
        for page in generator:
            if option.nesting != None:
                if page.title().count('/') > option.nesting-1:
                    # page to deep
                    continue
            title = self.getTitle(page, option)
            if not option.targets or self.getTitle(page, option) not in redirectpages:
                pages.append('"'+title+'"')
            else:
                #options.targets AND in redirectpages
                text = '{ seed="'+title+'", shift="'+redirectpages.get(title)+'" }'
                pages.append(text)
                pass
        pass

        luaText  = 'return {'+"\n"
        luaText += 'stamp = "'+timestamp+'",  -- [[User:EfenBot]]'+"\n"
        luaText += 'pages = {'+"\n"
        luaText += ",\n".join(pages) +"\n" #Liste der Seiten
        luaText += '}    -- pages { }'+"\n"
        luaText += '};'+"\n"
        
        return luaText
    def getTitle(self, page, option):
        if option.stripprefix:
            title = page.title(withNamespace=False)
            title = option.add_prefix+title.replace(option.prefix,"",1)
        else:
            title = page.title()
        return title
        pass
    
if __name__ == "__main__":
    try:
        pywikibot.output("PageTreeSupplier by se4598")
        botmode = False
        sandbox = False
        for arg in pywikibot.handleArgs():
            if arg.startswith("-botmode"):
                botmode = True
            if arg.startswith("-sandbox"):
                sandbox = True
            pass
        if botmode:
            pywikibot.output("running in botmode w/o confirm edit\n")
            pageTreeSupplier().run(confirmEdit=False, sandbox=sandbox)
        else:
            pywikibot.output("Manual mode\n")
            pageTreeSupplier().run(confirmEdit=True, sandbox=sandbox)
    finally:
        pywikibot.stopme()
