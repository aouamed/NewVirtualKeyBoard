#!/usr/bin/python
# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor

def main(session, **kwargs):
        from VirtualKeyBoard import nvKeyboardSetup
	session.open(nvKeyboardSetup)
	
def menu(menuid, **kwargs):
    if menuid == 'system':
        return [(_('VirtualKeyBoard setup'),
          main,
          'virtulkeyBoard_setup',
          None)]
    else:
        return []

def Plugins(**kwargs):
    return [PluginDescriptor(name=_('VirtualKeyBoard'), description=_('setup virtual keyboard'), where=PluginDescriptor.WHERE_MENU, needsRestart=False, fnc=menu)]
