#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
from urllib import quote
from enigma import loadPNG, ePoint, gRGB, eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER, getDesktop, RT_WRAP
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import NumberActionMap, ActionMap
from Components.HTMLComponent import *
from Components.GUIComponent import GUIComponent
from Components.Language import language
from Components.config import config, ConfigText, ConfigSubsection, ConfigSelection, ConfigYesNo, getConfigListEntry, configfile
from Components.ConfigList import ConfigListScreen
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Label import Label
from Components.Input import Input
from Components.Pixmap import Pixmap
from Tools.LoadPixmap import LoadPixmap
from skin import loadSkin
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LIBDIR

config.NewVirtualKeyBoard = ConfigSubsection()
config.NewVirtualKeyBoard.keys_layout = ConfigText(default='', fixed_size=False)
config.NewVirtualKeyBoard.lastsearchText = ConfigText(default='Enter search word', fixed_size=False)
config.NewVirtualKeyBoard.firsttime = ConfigYesNo(default=True)
config.NewVirtualKeyBoard.textinput = ConfigSelection(default='VirtualKeyBoard', choices=[('VirtualKeyBoard', _('Image virtual keyboard')), ('NewVirtualKeyBoard', _('New Virtual Keyboard'))])
config.NewVirtualKeyBoard.showsuggestion = ConfigYesNo(default=True)

def getDesktopSize():
	s = getDesktop(0).size()
	return (s.width(), s.height())

def isHD():
	desktopSize = getDesktopSize()
	return desktopSize[0] == 1280

def isFHD():
	desktopSize = getDesktopSize()
	return desktopSize[0] == 1920

if isFHD():
    skin_xml = '/usr/share/enigma2/NewVirtualKeyBoard/NewVirtualKeyBoardfhd.xml'
else:
    skin_xml = '/usr/share/enigma2/NewVirtualKeyBoard/NewVirtualKeyBoard.xml'

if os.path.exists(skin_xml):
    loadSkin(skin_xml)
    pass
else:
    print('skin.xml is not present')

vkLayoutDir = '/usr/share/enigma2/NewVirtualKeyBoard/kle/'
ServerUrl = 'http://tunisia-dreambox.info/TSplugins/NewVirtualKeyBoard/kle/'
hfile = '/etc/history'
parameters = {}
kblayout_loading_error='%s kblayout load failed'

def getLayoutFile(KBLayoutId):
    return vkLayoutDir + '%s.kle' % KBLayoutId

def getSLayoutFile(KBLayoutId):
    file = 'kle%s.kle' % KBLayoutId                    
    return ServerUrl  + file

def pathExists(path):
    if os.path.exists(path):
        return True
    else:
        return False

def downloadFile(url,target):
    import urllib2
    try:
        response = urllib2.urlopen(url,timeout=5)
        with open(target,'wb') as output:
          output.write(response.read())
        return True
    except:
        print("language download error")
        return False

def iconsDir(file=''):
    return '/usr/share/enigma2/NewVirtualKeyBoard/icons/' + file

class languageSelectionList(GUIComponent, object):

    def __init__(self):
        GUIComponent.__init__(self)
        self.l = eListboxPythonMultiContent()
        self.l.setBuildFunc(self.buildEntry)
        self.onSelectionChanged = []
        if isFHD():
            fontSize = 32
            itemHeight = 54
        else:
            fontSize = 24
            itemHeight = 46
        self.font = ('Regular', fontSize, itemHeight, 0)
        self.l.setFont(0, gFont('Regular', 60))
        self.l.setFont(1, gFont(self.font[0], self.font[1]))
        self.l.setItemHeight(self.font[2])
        self.dictPIX = {}

    def onCreate(self):
        pass

    def onDestroy(self):
        pass

    def connectSelChanged(self, fnc):
        if not fnc in self.onSelectionChanged:
            self.onSelectionChanged.append(fnc)

    def disconnectSelChanged(self, fnc):
        if fnc in self.onSelectionChanged:
            self.onSelectionChanged.remove(fnc)

    def selectionChanged(self):
        for x in self.onSelectionChanged:
            x()

    def getCurrent(self):
        cur = self.l.getCurrentSelection()
        return cur and cur[0]

    def postWidgetCreate(self, instance):
        instance.setContent(self.l)
        self.selectionChanged_conn = eConnectCallback(instance.selectionChanged, self.selectionChanged)
        self.onCreate()

    def preWidgetRemove(self, instance):
        instance.setContent(None)
        self.selectionChanged_conn = None
        self.onDestroy()

    def moveToIndex(self, index):
        self.instance.moveSelectionTo(index)

    def getCurrentIndex(self):
        return self.instance.getCurrentIndex()

    def setList(self, list):
        self.l.setList(list)

    def setSelectionState(self, enabled):
        self.instance.setSelectionEnable(enabled)

    def buildEntry(self, item):
        res = [None]
        width = self.l.getItemSize().width()
        height = self.l.getItemSize().height()
        y = (height - 16) / 2
        png='/usr/share/enigma2/NewVirtualKeyBoard/icons/menus/hd40/gey18.png'
        try:
            id=str(item['val'][2])
            if os.path.exists('/usr/share/enigma2/NewVirtualKeyBoard/kle/'+id+".kle"):
               png='/usr/share/enigma2/NewVirtualKeyBoard/icons/menus/hd40/green18.png' 
               res.append(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 3, y, 16, 16, loadPNG(png))
            else:
               png='/usr/share/enigma2/NewVirtualKeyBoard/icons/menus/hd40/grey18.png' 
               res.append(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 3, y, 16, 16, loadPNG(png))
            res.append(eListboxPythonMultiContent.TYPE_TEXT, 40, 0, width - 4, height, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(item['val'][0]))
        except Exception:
            pass
        return res
    GUI_WIDGET = eListbox
    currentIndex = property(getCurrentIndex, moveToIndex)
    currentSelection = property(getCurrent)

class KBLayoutLanguages:

    def __init__(self,LoadVKLayout_callback=None):
        self.defaultKBLAYOUT = defaultKBLAYOUT
        self.KbLayouts=KbLayouts
        self.KBLayoutId_installed=[]
        self.LoadVKLayout_callback=LoadVKLayout_callback
        self.KBsettings=config.NewVirtualKeyBoard

    def GetSystemLang(self,long=False):
        if long:
            try:
                defaultLanguage = language.getActiveLanguage()
            except Exception:
                pass
                defaultLanguage = 'en_EN'
        else:
            try:
                defaultLanguage = language.getActiveLanguage().split('_')[0]
            except Exception:
                defaultLanguage = 'en'
        return defaultLanguage

    def getDefault_KBLayout(self,KBLayoutId=''):
        if KBLayoutId == '':
            e2Locale = GetSystemLang(True)
            langMap = {'pl_PL': '00000415', 'en_EN': '00020409'}
            KBLayoutId = langMap.get(e2Locale, '')
            if KBLayoutId == '':
                for item in self.KbLayouts:
                    if e2Locale == item[1]:
                        KBLayoutId = item[2]
                        break
            if KBLayoutId == '':
                e2lang = GetSystemLang() + '_'
                for item in self.KbLayouts:
                    if item[1].startswith(e2lang):
                        KBLayoutId = item[2]
                        break
        return KBLayoutId 

    def saveInstalled_keylayout(self):
        self.KBLayoutId_installed=[]
        path = vkLayoutDir
        try:
            self.KBLayoutId_installed = [f for f in os.listdir(path) if os.path.isfile(f)]
        except:
            self.KBLayoutId_installed = []
        list1 = []
        if pathExists(path):
            for x in os.listdir(path):
                item = os.path.join(path, x)
                if os.path.isfile(item):
                    layoutid = x.replace('.kle', '')
                    self.KBLayoutId_installed.append(layoutid)
        else:
            self.KBLayoutId_installed = []

    def getActive_keylayout(self):
        selectedKBLayoutId = self.KBsettings.keys_layout.value
        return  selectedKBLayoutId

    def saveActive_keylayout(self,selectedKBLayoutId):
        if selectedKBLayoutId != self.KBsettings.keys_layout.value:
            self.KBsettings.keys_layout.value =selectedKBLayoutId
            self.KBsettings.keys_layout.save()
            configfile.save()
        self.saveInstalled_keylayout()    
        return selectedKBLayoutId

    def KeyLayoutExists(self,KBLayoutId):
        path = vkLayoutDir
        KBLayoutIdPath=path+KBLayoutId+'kle'
        if pathExists(path):
            return True
        else:
            return False

    def downloadKBlayout(self, KBLayoutId):
        ret=downloadFile(getSLayoutFile(KBLayoutId), getLayoutFile(KBLayoutId))
        return ret

    def setActive_Layout(self, KBLayoutId):
        loadErrorMsg = ''
        loadErrorNo=0
        loadSuccess=True
        filePath = vkLayoutDir + '%s.kle' % KBLayoutId
        if KBLayoutId == self.defaultKBLAYOUT['id']:
            self.LoadVKLayout_callback(self.defaultKBLAYOUT)
            return 0
        else:
            if pathExists(filePath):
                try:
                    from ast import literal_eval
                    import codecs
                    with codecs.open(filePath, encoding='utf-16') as f:
                        data = f.read()
                    data = literal_eval(data)
                    if data['id'] != KBLayoutId:
                        vkLayoutItem = self.getKeyboardLayoutItem(KBLayoutId)
                        raise Exception(_(kblayout_loading_error) % vkLayoutItem[0])
                        return 1
                    self.saveActive_keylayout(KBLayoutId)
                    self.LoadVKLayout_callback(data)
                    return 0
                except ImportError, e:
                    pass
            else:
                    loadErrorNo=2
            return loadErrorNo

    def getKeyboardLayoutItem(self, KBLayoutId):
        retItem = None
        for item in self.KbLayouts:
            if KBLayoutId == item[2]:
                retItem = item
                break
        return retItem 

    def getKeyboardLayoutFlag(self, KBLayoutId):
        lang = self.getKeyboardLayoutItem(KBLayoutId)
        try:
            lang = lang[1].split("_")[0]
        except:
            lang = 'noflag'
        flag = '/usr/share/enigma2/countries/' + lang + '.png'
        if not pathExists(flag):
           flag = '/usr/share/enigma2/countries/' +'noflag.png'
        return flag

class LanguageListScreen(Screen,KBLayoutLanguages):

    def __init__(self, session, listValue=[], selIdx=None,loadVKLayout_callback=None):
        Screen.__init__(self, session)
        self.loadVKLayout_callback=loadVKLayout_callback
        KBLayoutLanguages.__init__(self,LoadVKLayout_callback=self.loadVKLayout_callback)
        self.skinName = 'LanguageListScreen'
        self['languageList'] = languageSelectionList()
        self['actions'] = ActionMap(['ColorActions', 'WizardActions'],{
        'back': self.close,
        'ok': self.keyok,        
        }, -1)
        self['info']=Label(' ')
        self.languageList = self['languageList']
        self.languageList.onSelectionChanged.append(self.listselectionChanged)
        self.listselectionChanged=self.languageList.selectionChanged
        self.listValue=listValue
        self.selIdx=selIdx
        self.lastdownloaded_index=None
        self.onShown.append(self.settitle)

    def settitle(self):
        self.setTitle(_("Language selection"))
        self.showLanguageList()

    def listselectionChanged(self):
        cur=self.languageList.getCurrent()
        id=cur['val'][2]
        langFile=vkLayoutDir+str(id)+".kle"
        if pathExists(langFile):
               self['info'].setText(_('Press ok to remove language'))
        else:
               self['info'].setText(_('Press ok to install language')) 

    def showLanguageList(self,index=None):
        self.languageList.setList(self.listValue)
        self.languageList.setSelectionState(True)
        if index!=None:
            self.languageList.moveToIndex(index)
        elif self.selIdx != None:
            self.languageList.moveToIndex(self.selIdx)
        else:
            self.languageList.moveToIndex(0)
        self.languageList.show()

    def keyok(self):
        index = self.languageList.getCurrentIndex()
        cur=self.languageList.getCurrent()
        KBLayoutId=cur['val'][2]
        langFile=vkLayoutDir+str(KBLayoutId)+".kle"
        if pathExists(langFile):
               os.remove(langFile)
               self.showLanguageList(index)
               self['info'].setText(_('Language removed from installed package'))
               activeKBLayoutId=self.getActive_keylayout()
               if activeKBLayoutId==KBLayoutId:
                  KBLayoutId=self.getDefault_KBLayout()
               else:
                  KBLayoutId=activeKBLayoutId 
               self.setActive_Layout(KBLayoutId)    
        else: 
               index = self.languageList.getCurrentIndex()
               ret=self.downloadKBlayout(KBLayoutId)
               if ret:
                   self.showLanguageList(index)
                   self['info'].setText(_('Language downloaded successfully ,exit to install'))
                   self.setActive_Layout(KBLayoutId)
               else:
                   self['info'].setText(_('Failed to download language,try later'))

    def exit(self):
        self.close()

class eConnectCallbackObj:
    OBJ_ID = 0
    OBJ_NUM = 0
    def __init__(self, obj=None, connectHandler=None):
        eConnectCallbackObj.OBJ_ID += 1
        eConnectCallbackObj.OBJ_NUM += 1
        self.objID = eConnectCallbackObj.OBJ_ID
        self.connectHandler = connectHandler
        self.obj = obj

    def __del__(self):
        eConnectCallbackObj.OBJ_NUM -= 1
        try:
            if 'connect' not in dir(self.obj):
                if 'get' in dir(self.obj):
                    self.obj.get().remove(self.connectHandler)
                else:
                    self.obj.remove(self.connectHandler)
            else:
                del self.connectHandler
        except Exception:
            pass
        self.connectHandler = None
        self.obj = None

def eConnectCallback(obj, callbackFun, withExcept=False):
    try:
        if 'connect' in dir(obj):
            return eConnectCallbackObj(obj, obj.connect(callbackFun))
        else:
            if 'get' in dir(obj):
                obj.get().append(callbackFun)
            else:
                obj.append(callbackFun)
            return eConnectCallbackObj(obj, callbackFun)
    except Exception:
        pass
    return eConnectCallbackObj()

def TranslateTXT(txt):
    return txt
_ = TranslateTXT

def mkdirs(newdir, raiseException=False):
    try:
        if os.path.isdir(newdir):
            pass
        elif os.path.isfile(newdir):
            raise OSError("cannot create directory, file already exists: '%s'"
                           % newdir)
        else:
            (head, tail) = os.path.split(newdir)
            if head and not os.path.isdir(head) and not os.path.ismount(head) and not os.path.islink(head):
                mkdirs(head)
            if tail:
                os.mkdir(newdir)
        return True
    except Exception as e:
        if raiseException:
            raise e
    return False

def GetSystemLang(long=False):
    if long:
        try:
            defaultLanguage = language.getActiveLanguage()
        except Exception:
            pass
            defaultLanguage = 'en_EN'
    else:
        try:
            defaultLanguage = language.getActiveLanguage().split('_')[0]
        except Exception:

            defaultLanguage = 'en'
    return defaultLanguage

class textINput(Input):

    def __init__(self, *args, **kwargs):
        self.nvkTimeoutCallback = None
        Input.__init__(self, *args, **kwargs)

    def timeout(self, *args, **kwargs):
        callCallback = False
        try:
            callCallback = (True if self.lastKey != -1 else False)
        except Exception:
            pass
        try:
            Input.timeout(self, *args, **kwargs)
        except Exception:
            pass
        if self.nvkTimeoutCallback:
            self.nvkTimeoutCallback()

class textInputSuggestions:

    def __init__(self, callback=None, hl='en'):
        self.hl = hl
        self.conn = None
        self.callback = callback
        return

    def prepareQuery(self):
        self.prepQuerry = '/complete/search?output=chrome&client=chrome&'
        if self.hl is not None:
            self.prepQuerry = self.prepQuerry + 'hl=' + self.hl + '&'
        self.prepQuerry = self.prepQuerry + 'jsonp=self.gotSuggestions&q='
        return

    def dataError(self, error):
        print('unable to get suggestion')
        self.callback([])

    def parseGoogleData(self, output):
        try:
            if output:
                data = output
                charset = 'ISO-8859-1'
                if self.hl == 'ar' :
                    charset = 'windows-1256'
                   
                if  self.hl == 'fa':
                    charset = 'windows-1256'
                elif self.hl == 'el':
                    charset = 'windows-1253'
                elif self.hl == 'ru':
                    charset = 'windows-1251'                 
                try:
                    data = str(data.decode(charset)).encode('utf-8')
                except:
                    pass
                list = data.split(',')
                data2 = []
                for item in list:
                    if self.queryString in item:
                        item = item.replace('"', '').replace('[', '').replace(']', '').replace('self.gotSuggestions(', '')
                        data2.append(item)
                self.setGoogleSuggestions(data2)
            else:
                self.callback([])
        except:
            pass
        return

    def getGoogleSuggestions(self, queryString, hl='en'):
        self.hl = hl
        self.prepareQuery()
        self.queryString = queryString
        from twisted.internet import reactor
        from twisted.web.client import getPage
        self.reactor = reactor
        if queryString is not '':
            query = self.prepQuerry + quote(queryString)
            url = 'http://www.google.com' + query
            url = 'http://suggestqueries.google.com/complete/search?output=firefox&hl=%s&gl=%s%s&q=%s' % (self.hl, self.hl, '&ds=yt' if True else '', quote(queryString))
            getPage(url, headers={'Content-Type': 'application/x-www-form-urlencoded'}).addCallback(self.parseGoogleData).addErrback(self.dataError)
        else:
            return []

    def displaySearchHistory(self, word=None):
        try:
            if not os.path.exists(hfile):
                return []
            lines = open(hfile).readlines()
            list1 = []
            if len(lines) == 0:
                return []
            if word and  word != '':
                word = word.lower().strip()
                for line in lines:
                    line = line.strip()
                    if line  !='':
                        if line.startswith(word):
                            list1.insert(0,line)
                        else:
                            list1.append(line)
            if not word or word.strip()=='':
                for line in lines:
                    line = line.strip()
                    list1.append(line)
            return list1
        except:
            pass

    def clearSearchHistory(self):
        if os.path.exists(hfile):
            os.remove(hfile)
            return

    def saveSearchHistory(self, txt):
        try:
            if not os.path.exists(hfile):
                afile = open(hfile, 'w')
                afile.write(txt)
                afile.close()
                return
            L = list()
            f = open(hfile, 'r')
            for line in f.readlines():
                if txt == line.strip():
                    f.close()
                    return
                L.append(line)
            L.insert(0, txt + '\n')
            f.close()
            fi = open(hfile, 'w')
            for line in xrange(len(L)):
                if L[line].strip() !='':
                   fi.write(L[line])
            fi.close()
        except:
            print('error writing to history')

class selectList(GUIComponent, object):

    def __init__(self):
        GUIComponent.__init__(self)
        self.l = eListboxPythonMultiContent()
        self.l.setBuildFunc(self.buildEntry)
        self.onSelectionChanged = []
        if isFHD():
            fontSize = 32
            itemHeight = 54
        else:
            fontSize = 24
            itemHeight = 46
        self.font = ('Regular', fontSize, itemHeight, 0)
        self.l.setFont(0, gFont('Regular', 60))
        self.l.setFont(1, gFont(self.font[0], self.font[1]))
        self.l.setItemHeight(self.font[2])
        self.dictPIX = {}

    def onCreate(self):
        pass

    def onDestroy(self):
        pass

    def connectSelChanged(self, fnc):
        if not fnc in self.onSelectionChanged:
            self.onSelectionChanged.append(fnc)

    def disconnectSelChanged(self, fnc):
        if fnc in self.onSelectionChanged:
            self.onSelectionChanged.remove(fnc)

    def selectionChanged(self):
        for x in self.onSelectionChanged:
            x()

    def getCurrent(self):
        cur = self.l.getCurrentSelection()
        return cur and cur[0]

    def postWidgetCreate(self, instance):
        instance.setContent(self.l)
        self.selectionChanged_conn = eConnectCallback(instance.selectionChanged, self.selectionChanged)
        self.onCreate()

    def preWidgetRemove(self, instance):
        instance.setContent(None)
        self.selectionChanged_conn = None
        self.onDestroy()

    def moveToIndex(self, index):
        self.instance.moveSelectionTo(index)

    def getCurrentIndex(self):
        return self.instance.getCurrentIndex()

    def setList(self, list):
        self.l.setList(list)

    def setSelectionState(self, enabled):
        self.instance.setSelectionEnable(enabled)

    def buildEntry(self, item):
        res = [None]
        width = self.l.getItemSize().width()
        height = self.l.getItemSize().height()
        try:
            res.append((eListboxPythonMultiContent.TYPE_TEXT, 4, 0, width - 4, height, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, item))
        except Exception:
            pass
        return res
    GUI_WIDGET = eListbox
    currentIndex = property(getCurrentIndex, moveToIndex)
    currentSelection = property(getCurrent)

class createPixmap(Pixmap):

    def __init__(self):
        Pixmap.__init__(self)
        self.visible = True

    def setPixmap(self, ptr):
        self.instance.setPixmap(ptr)

class kb_layoutComponent:

    def __init__(self):
        self.SK_NONE = 0
        self.SK_SHIFT = 1
        self.SK_CTRL = 2
        self.SK_ALT = 4
        self.SK_CAPSLOCK = 8
        self.LEFT_KEYS = [1, 0x10, 30, 43, 56]
        self.RIGHT_KEYS = [15, 29, 42, 55, 62]
        self.KbLayouts = KbLayouts

    def createKID(self):
        self.keyidMap = KBlayoutKeyID
        self.defaultKBLAYOUT = defaultKBLAYOUT

    def drawKeyMap(self):
        self.keys_pixmap = {}
        self.FHDSkin = getDesktop(0).size().width() == 1920
        for key in kbSkeysList:
            self.keys_pixmap[key] = LoadPixmap(iconsDir(('nvk_hd/%s.png' if self.FHDSkin else 'nvk/%s.png')) % key)
        for i in range(0, 63):
            try:
                self[str(i)] = createPixmap()
            except:
                pass
        for key in pixmapKeys:
            self[key] = createPixmap()

        for i in range(1, 63):
            self['_%s' % i] = Label(' ')

        for m in range(6):
            self['m_%d' % m] = Label(' ')
        self.keys_pixmapMap = SkeysMap
        self.markerMap = markerMap
        self.colMax = len(self.keyidMap[0])
        self.rowMax = len(self.keyidMap)
        self.rowIdx = 0
        self.colIdx = 0
        self.colors = colors
        self.specialKeyState = self.SK_NONE

class NewVirtualKeyBoard(Screen, textInputSuggestions, kb_layoutComponent,KBLayoutLanguages):

    def __init__(self, session, title='', text=''):
        self.session = session
        self.focus_constants()
        kb_layoutComponent.__init__(self)
        KBLayoutLanguages.__init__(self,LoadVKLayout_callback=self.loadVKLayout)
        self.createKID()
        self.drawKeyMap()
        lastSearchedText=''
        if text.strip()=='':
            text=self.KBsettings.lastsearchText.value
        try:self.showsuggestion = self.KBsettings.showsuggestion.value
        except:self.showsuggestion=True
        self.showHistory=self.showsuggestion
        self.showHistory=self.showsuggestion
        self.googleSuggestionList=[]
        print("self.showsuggestion",self.showsuggestion)
        self.skinName = 'NewVirtualKeyBoard'
        Screen.__init__(self, session)
        textInputSuggestions.__init__(self, callback=self.setGoogleSuggestions)
        self.beforeUpdateText = ''
        self.onLayoutFinish.append(self.loadKBpixmaps)
        self.onShown.append(self.onWindowShow)
        self.onClose.append(self.__onClose)
        self['suggestionList'] = selectList()
        self['actions'] = self.getActionMap()
        self['historyheader'] = Label(' ')
        self['historyList'] = selectList()
        self.getinstalledkeylayout()
        self.counter = 0
        self['suggestionheader'] = Label(' ')
        self['historyheader'] = Label(' ')
        self.header = (title if title else _('Enter search text'))
        self.startText = text
        self['text'] = textINput(text=text)
        self['header'] = Label(' ')
        self['flag'] = Pixmap()
        self.currentVKLayout = self.defaultKBLAYOUT
        self.selectedKBLayoutId = self.KBsettings.keys_layout.value
        self.emptykey = u''
        self.vkRequestedId = ''
        self.focus = self.keyboard_hasfocus

    def getActionMap(self):
        return NumberActionMap(['WizardActions', 'DirectionActions', 'ColorActions', 'KeyboardInputActions', 'InputBoxActions', 'InputAsciiActions','SetupActions', 'MenuActions',], {
            'gotAsciiCode': self.keyGotAscii,
            'ok': self.keyOK,
            'ok_repeat': self.keyOK,
            'back': self.keyBack,
            'left': self.keyLeft,
            'right': self.keyRight,
            'up': self.keyUp,
            'down': self.keyDown,
            'red': self.keyRed,
            'red_repeat': self.keyRed,
            'green': self.keyGreen,
            'yellow': self.switchinstalledvklayout,
            'blue': self.togglesfocus,            
            'deleteBackward': self.backClicked,
            'deleteForward': self.forwardClicked,
            'pageUp': self.insertSpace,            
            'menu': self.listmenuoptions,
            'info': self.showHelp,
            'pageDown': self.clearText,
            '1': self.keyNumberGlobal,
            '2': self.keyNumberGlobal,
            '3': self.keyNumberGlobal,
            '4': self.keyNumberGlobal,
            '5': self.keyNumberGlobal,
            '6': self.keyNumberGlobal,
            '7': self.keyNumberGlobal,
            '8': self.keyNumberGlobal,
            '9': self.keyNumberGlobal,
            '0': self.keyNumberGlobal,
            }, -2)

    def onWindowShow(self):
        self.searchHistoryList = self.displaySearchHistory()
        self.showSearchHistory()
        self.onShown.remove(self.onWindowShow)
        self.setTitle(_('New Virtual Keyboard'))
        self['header'].setText(self.header)
        self['historyList'].setSelectionState(False)
        self['historyheader'].setText('Search history')
        self['suggestionList'].setSelectionState(False)
        self['suggestionheader'].setText('Google suggestion')
        self.setSuggestionVisible()
        self.isshowsuggestionEnabled = self.showsuggestion
        self.setText(self.startText)
        self.loadKBLayout()
        if self.KBsettings.firsttime.value==True:
            self.KBsettings.firsttime.value=False
            self.KBsettings.firsttime.save()
            self.showHelp()

    def __onClose(self):
        self.onClose.remove(self.__onClose)
        self['text'].nvkTimeoutCallback = None
        if self.selectedKBLayoutId != self.KBsettings.keys_layout.value:
            self.KBsettings.keys_layout.value = self.selectedKBLayoutId
            self.KBsettings.keys_layout.save()
            configfile.save()

    def focus_constants(self):
        self.history_hasfocus = 1
        self.keyboard_hasfocus = 0
        self.suggestion_hasfocus = 2

    def clearText(self):
            self["text"].deleteAllChars()
            self["text"].update()
            self.input_updated()

    def insertSpace(self):
        self.processKeyId(59)

    def loadKBLayout(self):
        KBLayoutId = (self.vkRequestedId if self.vkRequestedId else self.selectedKBLayoutId)
        KBLayoutId=self.getDefault_KBLayout(KBLayoutId)
        if not self.getKeyboardLayoutItem(KBLayoutId):
            KBLayoutId = self.selectedKBLayoutId
        self.getKeyboardLayout(KBLayoutId)

    def setText(self, text):
        self['text'].setText(text)
        self['text'].right()
        self['text'].currPos = len(text.decode('utf-8'))
        self['text'].right()
        self.input_updated()

    def loadKBpixmaps(self):
        self.onLayoutFinish.remove(self.loadKBpixmaps)
        self['text'].nvkTimeoutCallback = self.input_updated
        for i in range(0, 63):
            key = self.keys_pixmapMap.get(str(i), 'k')
            self[str(i)].setPixmap(self.keys_pixmap[key])
        for key in ['tmkey', 'mkey', 'mmkey', 'lmkey']:
            self[key].hide()
            self[key].setPixmap(self.keys_pixmap[key])
        self['b'].setPixmap(self.keys_pixmap['b'])
        self['l'].setPixmap(self.keys_pixmap['l'])
        self.currentKeyId = self.keyidMap[self.rowIdx][self.colIdx]
        self.move_KMarker(-1, self.currentKeyId)
        self.showSpecialText()

    def showSpecialText(self):
        self['_1'].setText('Esc')
        self['_16'].setText(_('Clear'))
        self['_29'].setText('Del')
        self['_30'].setText('Caps')
        self['_42'].setText('Enter')
        self['_43'].setText('Shift')
        self['_55'].setText('Shift')
        self['_57'].setText('Ctrl')
        self['_58'].setText('Alt')
        self['_60'].setText('Alt')
        self['_61'].setText(u'\u2190'.encode('utf-8'))
        self['_62'].setText(u'\u2192'.encode('utf-8'))

    def processArrowKey(self, dx=0, dy=0):
        oldKeyId = self.keyidMap[self.rowIdx][self.colIdx]
        keyID = oldKeyId
        if dx != 0 and keyID == 0:
            return
        if dx != 0:
            colIdx = self.colIdx
            while True:
                colIdx += dx
                if colIdx < 0:
                    colIdx = self.colMax - 1
                elif colIdx >= self.colMax:
                    colIdx = 0
                if keyID != self.keyidMap[self.rowIdx][colIdx]:
                    self.colIdx = colIdx
                    break
        elif dy != 0:
            rowIdx = self.rowIdx
            while True:
                rowIdx += dy
                if rowIdx < 0:
                    rowIdx = self.rowMax - 1
                elif rowIdx >= self.rowMax:
                    rowIdx = 0
                if keyID != self.keyidMap[rowIdx][self.colIdx]:
                    self.rowIdx = rowIdx
                    break
        if dx != 0:
            keyID = self.keyidMap[self.rowIdx][self.colIdx]

            maxKeyX = self.colIdx
            for idx in range(self.colIdx + 1, self.colMax):
                if keyID == self.keyidMap[self.rowIdx][idx]:
                    maxKeyX = idx
                else:
                    break
            minKeyX = self.colIdx
            for idx in range(self.colIdx - 1, -1, -1):
                if keyID == self.keyidMap[self.rowIdx][idx]:
                    minKeyX = idx
                else:
                    break
            if maxKeyX - minKeyX > 2:
                self.colIdx = (maxKeyX + minKeyX) / 2
        self.currentKeyId = self.keyidMap[self.rowIdx][self.colIdx]
        self.move_KMarker(oldKeyId, self.currentKeyId)

    def move_KMarker(self, oldKeyId, newKeyId):
        if oldKeyId == -1 and newKeyId == -1:
            for key in ['tmkey', 'mkey', 'mmkey', 'lmkey']:
                self[key].hide()
            return
        if oldKeyId != -1:
            keyid = str(oldKeyId)
            marker = self.markerMap.get(keyid, 'mkey')
            self[marker].hide()
        if newKeyId != -1:
            keyid = str(newKeyId)
            marker = self.markerMap.get(keyid, 'mkey')
            self[marker].instance.move(ePoint(self[keyid].position[0],
                    self[keyid].position[1]))
            self[marker].show()

    def processKeyId(self, keyid):
        if keyid == 0:
            keyid = 42
        if keyid == 1:
            if self.emptykey:
                self.emptykey = u''
                self.updateKsText()
            else:
               self.close(None)
            return
        elif keyid == 15:
            self['text'].deleteBackward()
            self.input_updated()
            return
        elif keyid == 29:
            self['text'].delete()
            self.input_updated()
            return
        elif keyid == 0x10:
            self['text'].deleteAllChars()
            self['text'].update()
            self.input_updated()
            return
        elif keyid == 56:
            self.switchToLanguageSelection()
            return
        elif keyid == 61:
            self['text'].left()
            return
        elif keyid == 62:
            self['text'].right()
            return
        elif keyid == 42:
            try:
                text = self['text'].getText().decode('UTF-8').encode('UTF-8')
            except Exception:
                text = ''
                pass
            if  text.strip() !='':
                self.saveSearchHistory(text)
                self.KBsettings.lastsearchText.value=text
                self.KBsettings.lastsearchText.save()
            self.close(text)
            return
        elif keyid == 30:
            self.specialKeyState ^= self.SK_CAPSLOCK
            self.updateKsText()
            self.updateSKey([30], self.specialKeyState & self.SK_CAPSLOCK)
            return
        elif keyid in [43, 55]:
            self.specialKeyState ^= self.SK_SHIFT
            self.updateKsText()
            self.updateSKey([43, 55], self.specialKeyState & self.SK_SHIFT)
            return
        elif keyid in [58, 60]:
            self.specialKeyState ^= self.SK_ALT
            self.updateKsText()
            self.updateSKey([58, 60], self.specialKeyState & self.SK_ALT)
            return
        elif keyid == 57:
            self.specialKeyState ^= self.SK_CTRL
            self.updateKsText()
            self.updateSKey([57], self.specialKeyState & self.SK_CTRL)
            return
        else:
            updateKsText = False
            ret = 0
            text = u''
            val = self.getKeyChar(keyid)
            if val:
                for special in [(self.SK_CTRL, [57]), (self.SK_ALT, [58, 60]), (self.SK_SHIFT, [43, 55])]:
                    if self.specialKeyState & special[0]:
                        self.specialKeyState ^= special[0]
                        self.updateSKey(special[1], 0)
                        ret = None
                        updateKsText = True
            if val:
                if self.emptykey:
                    if val in self.currentVKLayout['deadkeys'].get(self.emptykey, {}):
                        text = self.currentVKLayout['deadkeys'][self.emptykey][val]
                    else:
                        text = self.emptykey + val
                    self.emptykey = u''
                    updateKsText = True
                elif val in self.currentVKLayout['deadkeys']:
                    self.emptykey = val
                    updateKsText = True
                else:
                    text = val
                self.insertText(text)
                ret = None
            if updateKsText:
                self.updateKsText()
            return ret
        return 0

    def getinstalledkeylayout(self):
        path = vkLayoutDir
        import os.path
        try:
            self.KBLayoutId_installed = [f for f in os.listdir(path) if os.path.isfile(f)]
        except:
            self.KBLayoutId_installed = []
        list1 = []
        if os.path.exists(path):
            for x in os.listdir(path):
                item = os.path.join(path, x)
                if os.path.isfile(item):
                    layoutid = x.replace('.kle', '')
                    self.KBLayoutId_installed.append(layoutid)
        else:
            self.KBLayoutId_installed = []

    def switchinstalledvklayout(self):
        try:
            self.counter = self.counter + 1
            if self.counter > len(self.KBLayoutId_installed) - 1:
                self.counter = 0
            if self.counter < 0:
                self.counter = len(self.KBLayoutId_installed) - 1
            KBLayoutId = self.KBLayoutId_installed[self.counter]
            self.selectedKBLayoutId = KBLayoutId
            self.getKeyboardLayout(KBLayoutId)
        except:
            pass

    def getKeyboardLayout(self,KBLayoutId):
        ret=self.setActive_Layout( KBLayoutId)
        if ret==1:
            vkLayoutItem = self.getKeyboardLayoutItem(KBLayoutId)
            self.session.open(MessageBox, text= _(kblayout_loading_error) % vkLayoutItem[0], type=MessageBox.TYPE_ERROR)
            return
        elif ret==2:
            success=self.downloadKBlayout(KBLayoutId)
            if not success:
                     self.loadVKLayout(self.defaultKBLAYOUT)
        self.displayActiveLayoutFlag(KBLayoutId)
                         
    def displayActiveLayoutFlag(self,KBLayoutId):
        flag=self.getKeyboardLayoutFlag(KBLayoutId)
        self['flag'].instance.setPixmapFromFile(flag)
        self['flag'].instance.show()                         

    def loadVKLayout(self, layout=None):
        if layout != None:
            self.currentVKLayout = layout
        self.updateKsText()
        self['_56'].setText(self.currentVKLayout['locale'].encode('UTF-8').split('-', 1)[0].upper())
        self['_56'].show()

    def updateSKey(self, keysidTab, state):
        if state:
            color = self.colors['color0']
        else:
            color = self.colors['color1']
        for keyid in keysidTab:
            self['_%s' % keyid].instance.setForegroundColor(color)

    def getKeyChar(self, keyid):
        state = self.specialKeyState
        if self.specialKeyState & self.SK_ALT and not self.specialKeyState & self.SK_CTRL:
			state ^= self.SK_CTRL
        key = self.currentVKLayout['layout'].get(keyid, {})
        if state in key:
            val = key[state]
        else:
            val = u''
        return val

    def updateNormalKText(self, keyid):
        val = self.getKeyChar(keyid)
        if not self.emptykey:
            if len(val) > 1:
                color = self.colors['color2']
            elif val in self.currentVKLayout['deadkeys']:
                color = self.colors['color3']
            else:
                color = self.colors['color1']
        elif val in self.currentVKLayout['deadkeys'].get(self.emptykey, {}):
            val = self.currentVKLayout['deadkeys'][self.emptykey][val]
            color = self.colors['color1']
        else:
            color = self.colors['color4']
        skinKey = self['_%s' % keyid]
        skinKey.instance.setForegroundColor(color)
        skinKey.setText(val.encode('utf-8'))

    def updateKsText(self):
        for rangeItem in [(2, 14), (17, 28), (31, 41), (44, 54), (59,59)]:
            for keyid in range(rangeItem[0], rangeItem[1] + 1):
                self.updateNormalKText(keyid)

    def showSearchHistory(self):
        if self.showHistory:
            leftList = self['historyList']
            leftList.setList([(x, ) for x in self.searchHistoryList])
            leftList.moveToIndex(0)
            leftList.show()
            self['historyheader'].setText(_('Search history'))
            self['historyheader'].show()

    def hideLefList(self):
        self['historyheader'].hide()
        self['historyList'].hide()
        self['historyList'].setList([])

    def switchToLanguageSelection(self):
        selIdx = None
        listValue = []
        for i in range(len(self.KbLayouts)):
            x = self.KbLayouts[i]
            if self.currentVKLayout['id'] == x[2]:
                sel = True
                selIdx = i
            else:
                sel = False
            listValue.append(({'sel': sel, 'val': x}, ))
        self.session.openWithCallback(self.languageSelectionBack,LanguageListScreen,listValue, selIdx,self.loadVKLayout)
      
    def languageSelectionBack(self,index=None):
        self.selectedKBLayoutId = self.getActive_keylayout()
        self.getKeyboardLayout(self.selectedKBLayoutId)
        self.switchToKayboard()
          
    def togglesfocus(self):
        if self.showsuggestion == False:
            return
        if self.focus == self.keyboard_hasfocus and  self.googleSuggestionList!=[]:
                 self.switchToGoogleSuggestions()
        elif  self.focus == self.keyboard_hasfocus and  self.googleSuggestionList==[] and self.searchHistoryList!=[]:
                 self.switchToSearchHistory() 
        elif self.focus == self.suggestion_hasfocus and   self.searchHistoryList!=[]:
                 self.switchToSearchHistory()
        elif self.focus == self.suggestion_hasfocus and   self.searchHistoryList==[] and self.googleSuggestionList!=[] :
                 self.switchToGoogleSuggestions()          
        elif self.focus == self.history_hasfocus:
                 self.switchToKayboard()

    def switchToKayboard(self):
        self.setFocus(self.keyboard_hasfocus)
        self.move_KMarker(-1, self.currentKeyId)

    def switchToGoogleSuggestions(self):
        if self.showsuggestion == True:
            self.setFocus(self.suggestion_hasfocus)
            self['suggestionList'].moveToIndex(0)
            self['suggestionList'].setSelectionState(True)
        else:
            self.switchToKayboard()

    def switchToSearchHistory(self):
        if self.showsuggestion == True:
            self.setFocus(self.history_hasfocus)
            self['historyList'].moveToIndex(0)
            self['historyList'].setSelectionState(True)
        else:
            self.switchToKayboard()

    def setFocus(self, focus):
        self['text'].timeout()
        if self.focus != focus:
            if self.focus == self.keyboard_hasfocus:
                self.move_KMarker(-1, -1)
            elif self.focus == self.suggestion_hasfocus:
                self['suggestionList'].setSelectionState(False)
            elif self.focus == self.history_hasfocus:
                self['historyList'].setSelectionState(False)
            self.focus = focus

    def keyRed(self):
        if self.focus == self.keyboard_hasfocus:
            self.processKeyId(15)
        else:
            return 0

    def keyGreen(self):
        self.processKeyId(42)

    def keyYellow(self):
        if self.focus == self.keyboard_hasfocus:
            self.processKeyId(60)
        else:
            return 0

    def keyBlue(self):
        if self.focus == self.keyboard_hasfocus:
            self.processKeyId(43)
        else:
            return 0

    def keyOK(self):
        if self.focus in (self.suggestion_hasfocus, self.history_hasfocus):
            text = self[('suggestionList' if self.focus == self.suggestion_hasfocus else 'historyList')].getCurrent()
            if text:
                self.setText(text)
            self.currentKeyId = 0
            self.rowIdx = 0
            self.colIdx = 7
            self.switchToKayboard()
        elif self.focus == self.keyboard_hasfocus:
            self.processKeyId(self.currentKeyId)
        else:
            return 0

    def keyBack(self):
        if self.focus == self.keyboard_hasfocus:
            if self.emptykey:
                self.emptykey = u''
                self.updateKsText()
            else:
                self.saveActive_keylayout(self.selectedKBLayoutId) 
                self.close(None)
        elif self.focus in (self.suggestion_hasfocus, self.history_hasfocus):
            self.switchToKayboard()
        else:
            return 0

    def keyUp(self):
        if self.focus == self.keyboard_hasfocus:
            self.processArrowKey(0, -1)
        elif self.focus == self.history_hasfocus:
            item = self['historyList']
            if item.instance is not None:
                item.instance.moveSelection(item.instance.moveUp)
        elif self.focus == self.suggestion_hasfocus:
            item = self['suggestionList']
            if item.instance is not None:
                item.instance.moveSelection(item.instance.moveUp)
        else:
            return 0

    def keyDown(self):
        if self.focus == self.keyboard_hasfocus:
            self.processArrowKey(0, 1)
        elif self.focus == self.history_hasfocus:
            item = self['historyList']
            if item.instance is not None:
                item.instance.moveSelection(item.instance.moveDown)
        elif self.focus == self.suggestion_hasfocus:
            item = self['suggestionList']
            if item.instance is not None:
                item.instance.moveSelection(item.instance.moveDown)
        else:
            return 0

    def keyLeft(self):
        if self.focus == self.history_hasfocus:
            if self.showsuggestion:
                self.switchToGoogleSuggestions()
            else:
                self.switchToKayboard()
                if self.currentKeyId in self.LEFT_KEYS:
                    self.processArrowKey(-1, 0)
        elif self.focus == self.suggestion_hasfocus:
            self.switchToKayboard()
            if self.currentKeyId in self.LEFT_KEYS:
                self.processArrowKey(-1, 0)
        elif self.focus == self.keyboard_hasfocus:
            if self.currentKeyId in self.LEFT_KEYS or self.currentKeyId == 0 and self['text'].currPos == 0:
                if self.showHistory and self.showsuggestion == True:
                    self.switchToSearchHistory()
                    return
                elif self.showsuggestion == True:
                    self.switchToGoogleSuggestions()
                    return
            if self.currentKeyId == 0:
                self['text'].left()
            else:
                self.processArrowKey(-1, 0)
        else:
            return 0

    def keyRight(self):
        if self.focus == self.history_hasfocus:
            self.switchToKayboard()
            if self.currentKeyId in self.RIGHT_KEYS:
                self.processArrowKey(1, 0)
        elif self.focus == self.suggestion_hasfocus:
            if self.showHistory:
                self.switchToSearchHistory()
            else:
                self.switchToKayboard()
                if self.currentKeyId in self.RIGHT_KEYS:
                    self.processArrowKey(1, 0)
        elif self.focus == self.keyboard_hasfocus:
            if self.currentKeyId in self.RIGHT_KEYS or self.currentKeyId == 0 and self['text'].currPos == len(self['text'].Text):
                if self.showsuggestion:
                    self.switchToGoogleSuggestions()
                    return
                elif self.showHistory:
                    self.switchToSearchHistory()
                    return
            if self.currentKeyId == 0:
                self['text'].right()
            else:
                self.processArrowKey(1, 0)
        else:
            return 0

    def cursorRight(self):
        if self.focus == self.keyboard_hasfocus:
            self.processKeyId(62)
        else:
            return 0

    def cursorLeft(self):
        if self.focus == self.keyboard_hasfocus:
            self.processKeyId(61)
        else:
            return 0

    def backClicked(self):
        if self.focus == self.keyboard_hasfocus:
            self.processKeyId(15)
        else:
            return 0

    def forwardClicked(self):
        if self.focus == self.keyboard_hasfocus:
            self.processKeyId(29)
        else:
            return 0

    def keyNumberGlobal(self, number):
        if self.currentKeyId == 0:
            try:
                self['text'].number(number)
            except Exception:
                pass

    def keyGotAscii(self):
        if self.currentKeyId == 0:
            try:
                self['text'].handleAscii(getPrevAsciiCode())
            except Exception:
                pass

    def setSuggestionVisible(self):
        if self.showsuggestion == True:
            self['suggestionheader'].show()
            self['suggestionList'].show()
            self['historyheader'].show()
            self['historyList'].show()
            self.showSearchHistory()
        else:
            self['suggestionheader'].hide()
            self['historyheader'].hide()
            self['suggestionList'].hide()
            self['historyList'].hide()

    def insertText(self, text):
        for letter in text:
            try:
                self['text'].insertChar(letter, self['text'].currPos, False, True)
                self['text'].innerright()
                self['text'].update()
            except Exception:
                pass
        self.input_updated()

    def input_updated(self):
        if self['text'].Text == self.beforeUpdateText:
            return
        else:
            self.beforeUpdateText = self['text'].Text
        self.updateGHSuggestions()

    def updateGHSuggestions(self):
        if not self['text'].Text:
            self.setSuggestionVisible()
            self['suggestionList'].setList([])
        else:
            self.getsuggestion()

    def getsuggestion(self):
        word = self['text'].getText()
        list1 = self.displaySearchHistory(word)
        self.searchHistoryList = list1
        if list1:
            self['historyList'].setList([(x, ) for x in list1])
        lang = self.getKeyboardLayoutItem(self.selectedKBLayoutId)
        try:
            lang = lang[1].split('_')[0]
        except:
            lang = 'en'
        self.getGoogleSuggestions(word, hl=lang)

    def setGoogleSuggestions(self, list=[]):
        self.googleSuggestionList=list
        if list:
            self['suggestionList'].setList([(x, ) for x in list])
        self.setSuggestionVisible()

    def listmenuoptions(self):

        def getmenuData():
            menuData = []
            menuData.append((0, 'Install language', 'flag'))           
            menuData.append((1, 'Clear history', 'history'))
            menuData.append((2, 'Settings', 'settings'))
            return menuData

        def optionsback(index=None):
            if index == 0:
                self.switchToLanguageSelection()
            elif index == 2:
                self.session.openWithCallback(self.settings_back,nvKeyboardSetup)
                return
            if index == 1:
                self.clearSearchHistory()
                self['historyList'].setList([])
        self.session.openWithCallback(optionsback, vkOptionsScreen, _('select task'), getmenuData())
        return

    def settings_back(self,result=None):
        if result:
            self.showsuggestion=self.KBsettings.showsuggestion.value   
            self.setSuggestionVisible()
        
    def showHelp(self):

        def getmenuData():
            menuData = []
            menuData.append((0, 'Switch language-yellow button', 'yellow'))
            menuData.append((1, 'Insert space-pageup button', 'pageup'))
            menuData.append((2, 'Clear input text-pagedown button', 'pagedown'))           
            menuData.append((3, 'Toggle focus between suggestion,history,blue button', 'blue'))
            menuData.append((4, 'Show more functions-Installed language...', 'menu'))
            menuData.append((5, 'Show this screen again', 'info'))
            return menuData

        def optionsback(index=None):
            return
        self.session.openWithCallback(optionsback, vkOptionsScreen, _('Help'), getmenuData())
        return

class vkOptionsScreen(Screen):

    def __init__(self, session, title, datalist=[]):
        Screen.__init__(self, session)
        self.skinName = 'vkOptionsScreen'
        self['menu'] = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
        self['actions'] = ActionMap(['ColorActions', 'WizardActions'],{
        'back': self.close,
        'ok': self.exit,
        'back': self.close
        }, -1)
        self.settitle(title, datalist)

    def settitle(self, title, datalist):
        self.setTitle(title)
        self.showmenulist(datalist)

    def exit(self):
        index = self['menu'].getSelectionIndex()
        self.close(index)

    def showmenulist(self, datalist):
        cbcolor = 16753920
        cccolor = 15657130
        cdcolor = 16711680
        cecolor = 16729344
        cfcolor = 65407
        cgcolor = 11403055
        chcolor = 13047173
        cicolor = 13789470
        scolor = cbcolor
        res = []
        menulist = []
        if isHD():
            self['menu'].l.setItemHeight(50)
            self['menu'].l.setFont(0, gFont('Regular', 28))
        else:
            self['menu'].l.setItemHeight(75)
            self['menu'].l.setFont(0, gFont('Regular', 42))
        for i in range(0, len(datalist)):
            txt = datalist[i][1]
            if isHD():
                png = os.path.join('/usr/share/enigma2/NewVirtualKeyBoard/icons/menus/hd40/%s.png' % datalist[i][2])
            else:
                png = os.path.join('/usr/share/enigma2/NewVirtualKeyBoard/icons/menus/fhd75/%s.png' % datalist[i][2])
            res.append(MultiContentEntryText(pos=(0, 1), size=(0, 0), font=0, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text='', color=scolor, color_sel=cccolor, border_width=3, border_color=806544))
            if isHD():
                res.append(MultiContentEntryText(pos=(60, 1), size=(723, 50), font=0, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text=str(txt), color=16777215, color_sel=16777215))
                res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(40, 40), png=loadPNG(png)))
            else:
                res.append(MultiContentEntryText(pos=(100, 1), size=(1080, 75), font=0, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, text=str(txt), color=16777215, color_sel=16777215))
                res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(75, 75), png=loadPNG(png)))
            menulist.append(res)
            res = []
        self['menu'].l.setList(menulist)
        self['menu'].show()

class nvKeyboardSetup(ConfigListScreen, Screen):
    swidth=getDesktop(0).size().width()
    if isFHD():
	skin='''
	<screen name="nvKeyboardSetu" position="center,center" size="1080,540" backgroundColor="#16000000" title="New Virtual Keyboard  Settings">
		<ePixmap position="118,482" size="38,38" pixmap="~/images/red.png" zPosition="3" transparent="1" alphatest="blend" />
		<ePixmap position="424,482" size="38,38" pixmap="~/images/green.png" zPosition="3" transparent="1" alphatest="blend" />
		<ePixmap position="724,482" size="38,38" pixmap="~/images/blue.png" zPosition="3" transparent="1" alphatest="blend" />
		<eLabel position="60,468" zPosition="4" size="300,36" halign="center" font="Regular;33" transparent="1" foregroundColor="#ffffff" backgroundColor="#41000000" text="Cancel" />
		<eLabel position="368,468" zPosition="4" size="300,36" halign="center" font="Regular;33" transparent="1" foregroundColor="#ffffff" backgroundColor="#41000000" text="Save" />
		<eLabel position="735,468" zPosition="4" size="300,36" halign="center" font="Regular;30" transparent="1" foregroundColor="#ffffff" backgroundColor="#41000000" text="Virtual keyboard " />
				<widget name="config" position="30,75" size="1050,480" itemHeight="45" font="Regular;36" scrollbarMode="showOnDemand" transparent="1" zPosition="2" />
	</screen>'''
    else:
	skin='''
	<screen name="nvKeyboardSetu" position="center,center" size="719,360" backgroundColor="#16000000" title="New Virtual Keyboard  Settings">
		<ePixmap position="79,321" size="25,25" pixmap="~/images/red.png" zPosition="3" transparent="1" alphatest="blend" />
		<ePixmap position="282,321" size="25,25" pixmap="~/images/green.png" zPosition="3" transparent="1" alphatest="blend" />
		<ePixmap position="482,321" size="25,25" pixmap="~/images/blue.png" zPosition="3" transparent="1" alphatest="blend" />
		<eLabel position="40,322" zPosition="4" size="200,24" halign="center" font="Regular;22" transparent="1" foregroundColor="#ffffff" backgroundColor="#41000000" text="Cancel" />
		<eLabel position="245,322" zPosition="4" size="200,24" halign="center" font="Regular;22" transparent="1" foregroundColor="#ffffff" backgroundColor="#41000000" text="Save" />
		<eLabel position="490,322" zPosition="4" size="200,24" halign="center" font="Regular;20" transparent="1" foregroundColor="#ffffff" backgroundColor="#41000000" text="Virtual keyboard " />
		<widget name="config" position="20,50" size="699,320" scrollbarMode="showOnDemand" transparent="1" zPosition="2" />
	</screen>'''

    def __init__(self, session,fromkeyboard=False):
        Screen.__init__(self, session)
        self.list = []
        self.list = []
        pyo_link = resolveFilename(SCOPE_LIBDIR, "enigma2/python/Screens/VirtualKeyBoard.pyo")
        if not os.path.islink(pyo_link):
           config.NewVirtualKeyBoard.textinput.value="VirtualKeyBoard"
           config.NewVirtualKeyBoard.textinput.save()
        else:
           config.NewVirtualKeyBoard.textinput.value="NewVirtualKeyBoard"
           config.NewVirtualKeyBoard.textinput.save()
	self.skin_path = resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NewVirtualKeyBoard")
        self.fromkeyboard=fromkeyboard
        self['config']=MenuList([])
        ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changedEntry)
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions'], {'green': self.keySave,'blue':self.showkeyboard ,       
         'cancel': self.keyClose,"left": self.keyLeft,"right": self.keyRight,}, -2)
        self.currKeyoboard=config.NewVirtualKeyBoard.textinput.value
        self.createConfigList()

    def changedEntry(self):
            cur = self['config'].list[0]
            curval=cur[1].value
            print("curval",curval)
            if 'NewVirtualKeyBoard' ==curval:
                self.createConfigList(True)
            else:
                self.createConfigList(False)

    def createConfigList(self,value=False):
        self.list=[]
        self.list.append(getConfigListEntry(_('Text input method-keyboard:'), config.NewVirtualKeyBoard.textinput))
        if  config.NewVirtualKeyBoard.textinput.value=='NewVirtualKeyBoard' or value==True:
            self.list.append(getConfigListEntry(_('Show google and history suggestion:'), config.NewVirtualKeyBoard.showsuggestion))
        else:
            pass
        self['config'].list = self.list
        self['config'].l.setList(self.list)

    def keySave(self):
        for x in self['config'].list:
            x[1].save()
        configfile.save()
        pyo_link = resolveFilename(SCOPE_LIBDIR, "enigma2/python/Screens/VirtualKeyBoard.pyo")
        py_image = resolveFilename(SCOPE_LIBDIR, "enigma2/python/Screens/VirtualKeyBoard.py")
        py_backup = resolveFilename(SCOPE_LIBDIR, "enigma2/python/Screens/VirtualKeyBoard_backup.py")
        pyo_image = resolveFilename(SCOPE_LIBDIR, "enigma2/python/Screens/VirtualKeyBoard.pyo")
        pyo_backup = resolveFilename(SCOPE_LIBDIR, "enigma2/python/Screens/VirtualKeyBoard_backup.pyo")
        pyo_NewVirtualKeyBoard = resolveFilename(SCOPE_LIBDIR, "enigma2/python/Plugins/SystemPlugins/NewVirtualKeyBoard/VirtualKeyBoard.pyo")
        if not config.NewVirtualKeyBoard.textinput.value == self.currKeyoboard :
           if config.NewVirtualKeyBoard.textinput.value == "NewVirtualKeyBoard":
               if not os.path.islink(pyo_link):
                  if os.path.exists(py_image):
                     os.rename(py_image, py_backup)
                  if os.path.exists(pyo_image):
                     os.rename(pyo_image, pyo_backup)
                  os.symlink(pyo_NewVirtualKeyBoard, pyo_link)
           elif config.NewVirtualKeyBoard.textinput.value == "VirtualKeyBoard":
               if os.path.islink(pyo_link):
                  if os.path.exists(py_backup):
                     os.remove(pyo_link)
                     os.rename(py_backup, py_image)
                  elif os.path.exists(pyo_backup):
                     os.remove(pyo_link)
                     os.rename(pyo_backup, pyo_image)
               else:
                  pass
           self.session.openWithCallback(self.restartenigma, MessageBox, _('Restart enigma2 to load new settings?'), MessageBox.TYPE_YESNO)
        else:
               self.close(True)

    def showkeyboard(self):
        if self.fromkeyboard:
           self.close()
        else:
            from Screens.VirtualKeyBoard import VirtualKeyBoard
            self.session.open(VirtualKeyBoard)

    def restartenigma(self, result):
        if result:
            from Screens.Standby import TryQuitMainloop
            self.session.open(TryQuitMainloop, 3)
        else:
            self.close(True)

    def keyClose(self):
        for x in self['config'].list:
            x[1].cancel()
        self.close()

KbLayouts=[('Albanian', 'sq_AL', '0000041c'),
            ('Arabic (101)', 'ar_SA', '00000401'),
            ('Arabic (102)', 'ar_SA', '00010401'),
            ('Arabic (102) AZERTY', 'ar_SA', '00020401'),
            ('Armenian Eastern', 'hy_AM', '0000042b'),
            ('Armenian Western', 'hy_AM', '0001042b'),
            ('Assamese - INSCRIPT', 'as_IN', '0000044d'),
            ('Azeri Cyrillic', 'az_Cyrl-AZ', '0000082c'),
            ('Azeri Latin', 'az_Latn-AZ', '0000042c'),
            ('Bashkir', 'ba_RU', '0000046d'),
            ('Belarusian', 'be_BY', '00000423'),
            ('Belgian (Comma)', 'fr_BE', '0001080c'),
            ('Belgian (Period)', 'nl_BE', '00000813'),
            ('Belgian French', 'fr_BE', '0000080c'),
            ('Bengali', 'bn_IN', '00000445'),
            ('Bengali - INSCRIPT', 'bn_IN', '00020445'),
            ('Bengali - INSCRIPT (Legacy)', 'bn_IN', '00010445'),
            ('Bosnian (Cyrillic)', 'bs_Cyrl-BA', '0000201a'),
            ('Bulgarian', 'bg_BG', '00030402'),
            ('Bulgarian (Latin)', 'bg_BG', '00010402'),
            ('Bulgarian (Phonetic Traditional)', 'bg_BG', '00040402'),
            ('Bulgarian (Phonetic)', 'bg_BG', '00020402'),
            ('Bulgarian (Typewriter)', 'bg_BG', '00000402'),
            ('Canadian French', 'en_CA', '00001009'),
            ('Canadian French (Legacy)', 'fr_CA', '00000c0c'),
            ('Canadian Multilingual Standard', 'en_CA', '00011009'),
            ('Chinese (Simplified) - US Keyboard', 'zh_CN', '00000804'
             ),
            ('Chinese (Simplified, Singapore) - US Keyboard', 'zh_SG',
             '00001004'),
            ('Chinese (Traditional) - US Keyboard', 'zh_TW', '00000404'
             ),
            ('Chinese (Traditional, Hong Kong S.A.R.) - US Keyboard',
             'zh_HK', '00000c04'),
            ('Chinese (Traditional, Macao S.A.R.) - US Keyboard',
             'zh_MO', '00001404'),
            ('Croatian', 'hr_HR', '0000041a'),
            ('Czech', 'cs_CZ', '00000405'),
            ('Czech (QWERTY)', 'cs_CZ', '00010405'),
            ('Czech Programmers', 'cs_CZ', '00020405'),
            ('Danish', 'da_DK', '00000406'),
            ('Devanagari - INSCRIPT', 'hi_IN', '00000439'),
            ('Divehi Phonetic', 'dv_MV', '00000465'),
            ('Divehi Typewriter', 'dv_MV', '00010465'),
            ('Dutch', 'nl_NL', '00000413'),
            ('Estonian', 'et_EE', '00000425'),
            ('Faeroese', 'fo_FO', '00000438'),
            ('Finnish', 'fi_FI', '0000040b'),
            ('Finnish with Sami', 'se_SE', '0001083b'),
            ('French', 'fr_FR', '0000040c'),
            ('Gaelic', 'en_IE', '00011809'),
            ('Georgian', 'ka_GE', '00000437'),
            ('Georgian (Ergonomic)', 'ka_GE', '00020437'),
            ('Georgian (QWERTY)', 'ka_GE', '00010437'),
            ('German', 'de_DE', '00000407'),
            ('German (IBM)', 'de_DE', '00010407'),
            ('Greek', 'el_GR', '00000408'),
            ('Greek (220)', 'el_GR', '00010408'),
            ('Greek (220) Latin', 'el_GR', '00030408'),
            ('Greek (319)', 'el_GR', '00020408'),
            ('Greek (319) Latin', 'el_GR', '00040408'),
            ('Greek Latin', 'el_GR', '00050408'),
            ('Greek Polytonic', 'el_GR', '00060408'),
            ('Greenlandic', 'kl_GL', '0000046f'),
            ('Gujarati', 'gu_IN', '00000447'),
            ('Hausa', 'ha_Latn-NG', '00000468'),
            ('Hebrew', 'he_IL', '0000040d'),
            ('Hindi Traditional', 'hi_IN', '00010439'),
            ('Hungarian', 'hu_HU', '0000040e'),
            ('Hungarian 101-key', 'hu_HU', '0001040e'),
            ('Icelandic', 'is_IS', '0000040f'),
            ('Igbo', 'ig_NG', '00000470'),
            ('Inuktitut - Latin', 'iu_Latn-CA', '0000085d'),
            ('Inuktitut - Naqittaut', 'iu_Cans-CA', '0001045d'),
            ('Irish', 'en_IE', '00001809'),
            ('Italian', 'it_IT', '00000410'),
            ('Italian (142)', 'it_IT', '00010410'),
            ('Japanese', 'ja_JP', '00000411'),
            ('Kannada', 'kn_IN', '0000044b'),
            ('Kazakh', 'kk_KZ', '0000043f'),
            ('Khmer', 'km_KH', '00000453'),
            ('Korean', 'ko_KR', '00000412'),
            ('Kyrgyz Cyrillic', 'ky_KG', '00000440'),
            ('Lao', 'lo_LA', '00000454'),
            ('Latin American', 'es_MX', '0000080a'),
            ('Latvian', 'lv_LV', '00000426'),
            ('Latvian (QWERTY)', 'lv_LV', '00010426'),
            ('Lithuanian', 'lt_LT', '00010427'),
            ('Lithuanian IBM', 'lt_LT', '00000427'),
            ('Lithuanian Standard', 'lt_LT', '00020427'),
            ('Luxembourgish', 'lb_LU', '0000046e'),
            ('Macedonian (FYROM)', 'mk_MK', '0000042f'),
            ('Macedonian (FYROM) - Standard', 'mk_MK', '0001042f'),
            ('Malayalam', 'ml_IN', '0000044c'),
            ('Maltese 47-Key', 'mt_MT', '0000043a'),
            ('Maltese 48-Key', 'mt_MT', '0001043a'),
            ('Maori', 'mi_NZ', '00000481'),
            ('Marathi', 'mr_IN', '0000044e'),
            ('Mongolian (Mongolian Script)', 'mn_Mong-CN', '00000850'),
            ('Mongolian Cyrillic', 'mn_MN', '00000450'),
            ('Nepali', 'ne_NP', '00000461'),
            ('Norwegian', 'nb_NO', '00000414'),
            ('Norwegian with Sami', 'se_NO', '0000043b'),
            ('Oriya', 'or_IN', '00000448'),
            ('Pashto (Afghanistan)', 'ps_AF', '00000463'),
            ('Persian', 'fa_IR', '00000429'),
            ('Polish (214)', 'pl_PL', '00010415'),
            ('Polish (Programmers)', 'pl_PL', '00000415'),
            ('Portuguese', 'pt_PT', '00000816'),
            ('Portuguese (Brazilian ABNT)', 'pt_BR', '00000416'),
            ('Portuguese (Brazilian ABNT2)', 'pt_BR', '00010416'),
            ('Punjabi', 'pa_IN', '00000446'),
            ('Romanian (Legacy)', 'ro_RO', '00000418'),
            ('Romanian (Programmers)', 'ro_RO', '00020418'),
            ('Romanian (Standard)', 'ro_RO', '00010418'),
            ('Russian', 'ru_RU', '00000419'),
            ('Russian (Typewriter)', 'ru_RU', '00010419'),
            ('Sami Extended Finland-Sweden', 'se_SE', '0002083b'),
            ('Sami Extended Norway', 'se_NO', '0001043b'),
            ('Serbian (Cyrillic)', 'sr_Cyrl-CS', '00000c1a'),
            ('Serbian (Latin)', 'sr_Latn-CS', '0000081a'),
            ('Sesotho sa Leboa', 'nso_ZA', '0000046c'),
            ('Setswana', 'tn_ZA', '00000432'),
            ('Sinhala', 'si_LK', '0000045b'),
            ('Sinhala - Wij 9', 'si_LK', '0001045b'),
            ('Slovak', 'sk_SK', '0000041b'),
            ('Slovak (QWERTY)', 'sk_SK', '0001041b'),
            ('Slovenian', 'sl_SI', '00000424'),
            ('Sorbian Extended', 'hsb_DE', '0001042e'),
            ('Sorbian Standard', 'hsb_DE', '0002042e'),
            ('Sorbian Standard (Legacy)', 'hsb_DE', '0000042e'),
            ('Spanish', 'es_ES', '0000040a'),
            ('Spanish Variation', 'es_ES', '0001040a'),
            ('Swedish', 'sv_SE', '0000041d'),
            ('Swedish with Sami', 'se_SE', '0000083b'),
            ('Swiss French', 'fr_CH', '0000100c'),
            ('Swiss German', 'de_CH', '00000807'),
            ('Syriac', 'syr_SY', '0000045a'),
            ('Syriac Phonetic', 'syr_SY', '0001045a'),
            ('Tajik', 'tg_Cyrl-TJ', '00000428'),
            ('Tamil', 'ta_IN', '00000449'),
            ('Tatar', 'tt_RU', '00000444'),
            ('Telugu', 'te_IN', '0000044a'),
            ('Thai Kedmanee', 'th_TH', '0000041e'),
            ('Thai Kedmanee (non-ShiftLock)', 'th_TH', '0002041e'),
            ('Thai Pattachote', 'th_TH', '0001041e'),
            ('Thai Pattachote (non-ShiftLock)', 'th_TH', '0003041e'),
            ('Tibetan (PRC)', 'bo_CN', '00000451'),
            ('Turkish F', 'tr_TR', '0001041f'),
            ('Turkish Q', 'tr_TR', '0000041f'),
            ('Turkmen', 'tk_TM', '00000442'),
            ('US', 'en_US', '00000409'),
            ('US English Table for IBM Arabic 238_L', 'en_US',
             '00050409'),
            ('Ukrainian', 'uk_UA', '00000422'),
            ('Ukrainian (Enhanced)', 'uk_UA', '00020422'),
            ('United Kingdom', 'en_GB', '00000809'),
            ('United Kingdom Extended', 'cy_GB', '00000452'),
            ('United States-Dvorak', 'en_US', '00010409'),
            ('United States-Dvorak for left hand', 'en_US', '00030409'
             ),
            ('United States-Dvorak for right hand', 'en_US', '00040409'
             ),
            ('United States-International', 'en_US', '00020409'),
            ('Urdu', 'ur_PK', '00000420'),
            ('Uyghur', 'ug_CN', '00010480'),
            ('Uyghur (Legacy)', 'ug_CN', '00000480'),
            ('Uzbek Cyrillic', 'uz_Cyrl-UZ', '00000843'),
            ('Vietnamese', 'vi_VN', '0000042a'),
            ('Wolof', 'wo_SN', '00000488'),
            ('Yakut', 'sah_RU', '00000485'),
            ('Yoruba', 'yo_NG', '0000046a'),
            ]

defaultKBLAYOUT = {
            'layout': {
                2: {
                    0: u'`',
                    1: u'~',
                    8: u'`',
                    9: u'~',
                    },
                3: {
                    0: u'1',
                    1: u'!',
                    6: u'\xa1',
                    7: u'\xb9',
                    8: u'1',
                    9: u'!',
                    14: u'\xa1',
                    15: u'\xb9',
                    },
                4: {
                    0: u'2',
                    1: u'@',
                    6: u'\xb2',
                    8: u'2',
                    9: u'@',
                    14: u'\xb2',
                    },
                5: {
                    0: u'3',
                    1: u'#',
                    6: u'\xb3',
                    8: u'3',
                    9: u'#',
                    14: u'\xb3',
                    },
                6: {
                    0: u'4',
                    1: u'$',
                    6: u'\xa4',
                    7: u'\xa3',
                    8: u'4',
                    9: u'$',
                    14: u'\xa4',
                    15: u'\xa3',
                    },
                7: {
                    0: u'5',
                    1: u'%',
                    6: u'\u20ac',
                    8: u'5',
                    9: u'%',
                    14: u'\u20ac',
                    },
                8: {
                    0: u'6',
                    1: u'^',
                    6: u'\xbc',
                    8: u'6',
                    9: u'^',
                    14: u'\xbc',
                    },
                9: {
                    0: u'7',
                    1: u'&',
                    6: u'\xbd',
                    8: u'7',
                    9: u'&',
                    14: u'\xbd',
                    },
                10: {
                    0: u'8',
                    1: u'*',
                    6: u'\xbe',
                    8: u'8',
                    9: u'*',
                    14: u'\xbe',
                    },
                11: {
                    0: u'9',
                    1: u'(',
                    6: u'\u2018',
                    8: u'9',
                    9: u'(',
                    14: u'\u2018',
                    },
                12: {
                    0: u'0',
                    1: u')',
                    6: u'\u2019',
                    8: u'0',
                    9: u')',
                    14: u'\u2019',
                    },
                13: {
                    0: u'-',
                    1: u'_',
                    6: u'\xa5',
                    8: u'-',
                    9: u'_',
                    14: u'\xa5',
                    },
                14: {
                    0: u'=',
                    1: u'+',
                    6: u'\xd7',
                    7: u'\xf7',
                    8: u'=',
                    9: u'+',
                    14: u'\xd7',
                    15: u'\xf7',
                    },
                17: {
                    0: u'q',
                    1: u'Q',
                    6: u'\xe4',
                    7: u'\xc4',
                    8: u'Q',
                    9: u'q',
                    14: u'\xc4',
                    15: u'\xe4',
                    },
                18: {
                    0: u'w',
                    1: u'W',
                    6: u'\xe5',
                    7: u'\xc5',
                    8: u'W',
                    9: u'w',
                    14: u'\xc5',
                    15: u'\xe5',
                    },
                19: {
                    0: u'e',
                    1: u'E',
                    6: u'\xe9',
                    7: u'\xc9',
                    8: u'E',
                    9: u'e',
                    14: u'\xc9',
                    15: u'\xe9',
                    },
                20: {
                    0: u'r',
                    1: u'R',
                    6: u'\xae',
                    8: u'R',
                    9: u'r',
                    14: u'\xae',
                    },
                21: {
                    0: u't',
                    1: u'T',
                    6: u'\xfe',
                    7: u'\xde',
                    8: u'T',
                    9: u't',
                    14: u'\xde',
                    15: u'\xfe',
                    },
                22: {
                    0: u'y',
                    1: u'Y',
                    6: u'\xfc',
                    7: u'\xdc',
                    8: u'Y',
                    9: u'y',
                    14: u'\xdc',
                    15: u'\xfc',
                    },
                23: {
                    0: u'u',
                    1: u'U',
                    6: u'\xfa',
                    7: u'\xda',
                    8: u'U',
                    9: u'u',
                    14: u'\xda',
                    15: u'\xfa',
                    },
                24: {
                    0: u'i',
                    1: u'I',
                    6: u'\xed',
                    7: u'\xcd',
                    8: u'I',
                    9: u'i',
                    14: u'\xcd',
                    15: u'\xed',
                    },
                25: {
                    0: u'o',
                    1: u'O',
                    6: u'\xf3',
                    7: u'\xd3',
                    8: u'O',
                    9: u'o',
                    14: u'\xd3',
                    15: u'\xf3',
                    },
                26: {
                    0: u'p',
                    1: u'P',
                    6: u'\xf6',
                    7: u'\xd6',
                    8: u'P',
                    9: u'p',
                    14: u'\xd6',
                    15: u'\xf6',
                    },
                27: {
                    0: u'[',
                    1: u'{',
                    2: u'\x1b',
                    6: u'\xab',
                    8: u'[',
                    9: u'{',
                    10: u'\x1b',
                    14: u'\xab',
                    },
                28: {
                    0: u']',
                    1: u'}',
                    2: u'\x1d',
                    6: u'\xbb',
                    8: u']',
                    9: u'}',
                    10: u'\x1d',
                    14: u'\xbb',
                    },
                31: {
                    0: u'a',
                    1: u'A',
                    6: u'\xe1',
                    7: u'\xc1',
                    8: u'A',
                    9: u'a',
                    14: u'\xc1',
                    15: u'\xe1',
                    },
                32: {
                    0: u's',
                    1: u'S',
                    6: u'\xdf',
                    7: u'\xa7',
                    8: u'S',
                    9: u's',
                    14: u'\xa7',
                    15: u'\xdf',
                    },
                33: {
                    0: u'd',
                    1: u'D',
                    6: u'\xf0',
                    7: u'\xd0',
                    8: u'D',
                    9: u'd',
                    14: u'\xd0',
                    15: u'\xf0',
                    },
                34: {
                    0: u'f',
                    1: u'F',
                    8: u'F',
                    9: u'f',
                    },
                35: {
                    0: u'g',
                    1: u'G',
                    8: u'G',
                    9: u'g',
                    },
                36: {
                    0: u'h',
                    1: u'H',
                    8: u'H',
                    9: u'h',
                    },
                37: {
                    0: u'j',
                    1: u'J',
                    8: u'J',
                    9: u'j',
                    },
                38: {
                    0: u'k',
                    1: u'K',
                    8: u'K',
                    9: u'k',
                    },
                39: {
                    0: u'l',
                    1: u'L',
                    6: u'\xf8',
                    7: u'\xd8',
                    8: u'L',
                    9: u'l',
                    14: u'\xd8',
                    15: u'\xf8',
                    },
                40: {
                    0: u';',
                    1: u':',
                    6: u'\xb6',
                    7: u'\xb0',
                    8: u';',
                    9: u':',
                    14: u'\xb6',
                    15: u'\xb0',
                    },
                41: {
                    0: u"'",
                    1: u'"',
                    6: u'\xb4',
                    7: u'\xa8',
                    8: u"'",
                    9: u'"',
                    14: u'\xb4',
                    15: u'\xa8',
                    },
                44: {
                    0: u'z',
                    1: u'Z',
                    6: u'\xe6',
                    7: u'\xc6',
                    8: u'Z',
                    9: u'z',
                    14: u'\xc6',
                    15: u'\xe6',
                    },
                45: {
                    0: u'x',
                    1: u'X',
                    8: u'X',
                    9: u'x',
                    },
                46: {
                    0: u'c',
                    1: u'C',
                    6: u'\xa9',
                    7: u'\xa2',
                    8: u'C',
                    9: u'c',
                    14: u'\xa2',
                    15: u'\xa9',
                    },
                47: {
                    0: u'v',
                    1: u'V',
                    8: u'V',
                    9: u'v',
                    },
                48: {
                    0: u'b',
                    1: u'B',
                    8: u'B',
                    9: u'b',
                    },
                49: {
                    0: u'n',
                    1: u'N',
                    6: u'\xf1',
                    7: u'\xd1',
                    8: u'N',
                    9: u'n',
                    14: u'\xd1',
                    15: u'\xf1',
                    },
                50: {
                    0: u'm',
                    1: u'M',
                    6: u'\xb5',
                    8: u'M',
                    9: u'm',
                    14: u'\xb5',
                    },
                51: {
                    0: u',',
                    1: u'<',
                    6: u'\xe7',
                    7: u'\xc7',
                    },
                52: {
                    0: u'.',
                    1: u'>',
                    8: u'.',
                    9: u'>',
                    },
                53: {
                    0: u'/',
                    1: u'?',
                    6: u'\xbf',
                    8: u'/',
                    9: u'?',
                    14: u'\xbf',
                    },
                54: {
                    0: u'\\',
                    1: u'|',
                    2: u'\x1c',
                    6: u'\xac',
                    7: u'\xa6',
                    8: u'\\',
                    9: u'|',
                    10: u'\x1c',
                    14: u'\xac',
                    15: u'\xa6',
                    },
                59: {
                    0: u' ',
                    1: u' ',
                    2: u' ',
                    8: u' ',
                    9: u' ',
                    10: u' ',
                    },
                },
            'name': u'English (United States)',
            'locale': u'en-US',
            'id': u'00020409',
            'deadkeys': {
                u'~': {
                    u'a': u'\xe3',
                    u'A': u'\xc3',
                    u' ': u'~',
                    u'O': u'\xd5',
                    u'N': u'\xd1',
                    u'o': u'\xf5',
                    u'n': u'\xf1',
                    },
                u'`': {
                    u'a': u'\xe0',
                    u'A': u'\xc0',
                    u'e': u'\xe8',
                    u' ': u'`',
                    u'i': u'\xec',
                    u'o': u'\xf2',
                    u'I': u'\xcc',
                    u'u': u'\xf9',
                    u'O': u'\xd2',
                    u'E': u'\xc8',
                    u'U': u'\xd9',
                    },
                u'"': {
                    u'a': u'\xe4',
                    u'A': u'\xc4',
                    u'e': u'\xeb',
                    u' ': u'"',
                    u'i': u'\xef',
                    u'o': u'\xf6',
                    u'I': u'\xcf',
                    u'u': u'\xfc',
                    u'O': u'\xd6',
                    u'y': u'\xff',
                    u'E': u'\xcb',
                    u'U': u'\xdc',
                    },
                u"'": {
                    u'a': u'\xe1',
                    u'A': u'\xc1',
                    u'c': u'\xe7',
                    u'e': u'\xe9',
                    u' ': u"'",
                    u'i': u'\xed',
                    u'C': u'\xc7',
                    u'o': u'\xf3',
                    u'I': u'\xcd',
                    u'u': u'\xfa',
                    u'O': u'\xd3',
                    u'y': u'\xfd',
                    u'E': u'\xc9',
                    u'U': u'\xda',
                    u'Y': u'\xdd',
                    },
                u'^': {
                    u'a': u'\xe2',
                    u'A': u'\xc2',
                    u'e': u'\xea',
                    u' ': u'^',
                    u'i': u'\xee',
                    u'o': u'\xf4',
                    u'I': u'\xce',
                    u'u': u'\xfb',
                    u'O': u'\xd4',
                    u'E': u'\xca',
                    u'U': u'\xdb',
                    },
                },
            'desc': u'United States-International',
            }

KBlayoutKeyID=[(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15), (16, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29), (30, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 42), (43, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 55), (56, 56, 57, 58, 59, 59, 59, 59, 59, 59, 59, 59, 60, 61, 62)]
kbSkeysList = [
    'pb',
    'pr',
    'pg',
    'py',
    'l',
    'b',
    'e',
    'tmkey',
    'k',
    'mkey',
    'skey',
    'mmkey',
    'lskey',
    'lkey',
    'lmkey',
    ]
pixmapKeys = [
    'l',
    'b',
    'tmkey',
    'mkey',
    'mmkey',
    'lmkey',
    ]

SkeysMap = {
    '0': 'e',
    '1': 'skey',
    '15': 'skey',
    '29': 'skey',
    '57': 'skey',
    '58': 'skey',
    '60': 'skey',
    '61': 'skey',
    '62': 'skey',
    '59': 'lkey',
    '16': 'lskey',
    '30': 'lskey',
    '42': 'lskey',
    '43': 'lskey',
    '55': 'lskey',
    '56': 'lskey',
    }

markerMap = {
    '0': 'tmkey',
    '59': 'lmkey',
    '16': 'mmkey',
    '30': 'mmkey',
    '42': 'mmkey',
    '43': 'mmkey',
    '55': 'mmkey',
    '56': 'mmkey',
    }

colors = {
    'color1': gRGB(int('ffffff', 0x10)),
    'color0': gRGB(int('39b54a', 0x10)),
    'color3': gRGB(int('0275a0', 0x10)),
    'color2': gRGB(int('ed1c24', 0x10)),
    'color4': gRGB(int('979697', 0x10)),
    }

VirtualKeyBoard = NewVirtualKeyBoard
