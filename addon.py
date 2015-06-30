#! /usr/bin/env python
# -*- coding:utf-8-*-
#
#      Copyright (C) 2015 Yllar Pajus
#      http://pilves.eu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import os
import sys
import urlparse
import urllib2
import re

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import buggalo

URL = 'http://arhiiv.err.ee/'
ARCHIVE_ID = '31'

class ErrException(Exception):
  pass

class Err(object):
  def downloadUrl(self,url):
    for retries in range(0, 5):
      try:
        r = urllib2.Request(url.encode('iso-8859-1', 'replace'))
        r.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2')
        u = urllib2.urlopen(r, timeout = 30)
        contents = u.read()
        u.close()
        return contents
      except Exception, ex:
        if retries >= 4:
          raise ErrException(ex)
      
  def listErrCategory(self):
    url = URL
    buggalo.addExtraData('url', url)
    html = self.downloadUrl(url)
    if not html:
      raise ErrException(ADDON.getLocalizedString(200))
    
    items = list()
    for k in re.finditer('alamkategooria/([^/]+)">([^<]+)</a>',html):
      #fanart = self.downloadAndCacheFanart(key, None)
      item = xbmcgui.ListItem(k.group(2), iconImage=FANART)
      item.setProperty('Fanart_Image', FANART)
      items.append((PATH + '?seeria=%s' % k.group(1), item, True))
    xbmcplugin.addDirectoryItems(HANDLE, items)
    xbmcplugin.endOfDirectory(HANDLE)
      
  def listSeries(self,seeria):
    url = URL + '/alamkategooria/%s/' % seeria + ARCHIVE_ID
    buggalo.addExtraData('url', url)
    html = self.downloadUrl(url)
    if not html:
      raise ErrException(ADDON.getLocalizedString(203))
    
    items = list()
    if html:
      item = xbmcgui.ListItem('Üksikud saated', iconImage=FANART)
      item.setProperty('Fanart_Image', FANART)
      items.append((PATH + '?seeria=%s&saade=%s' % (seeria, 'show-category-single-files'), item, True))
    for s in re.finditer('seeria/([^/]+).*">([^<]+)</a>',html):
      item = xbmcgui.ListItem(s.group(2), iconImage=FANART)
      item.setProperty('Fanart_Image', FANART)
      items.append((PATH + '?seeria=%s&saade=%s' % (seeria,s.group(1)), item, True))
    xbmcplugin.addDirectoryItems(HANDLE, items)
    xbmcplugin.endOfDirectory(HANDLE)
    
    
  def listSaade(self,seeria,saade):
    if saade != 'show-category-single-files':
      url = URL + 'seeria/' + saade + '/' + seeria + '/' + ARCHIVE_ID + '/date-desc/koik'
    else:
      url = URL + saade + '/' + seeria + '/' + ARCHIVE_ID + '/date-desc/koik'
          
    buggalo.addExtraData('url', url)
    html = self.downloadUrl(url)
    
    items = list()
    for s in re.finditer('/vaata/([^"]+)">([^<]+)<.*fileDateInList">\(([^)]+)\)',html):

      title = s.group(2)
      date = s.group(3)
      
      infoLabels = {
        'date' : date,
        'title' : title
      }
      
      item = xbmcgui.ListItem(title, iconImage = FANART)
      item.setInfo('video', infoLabels)
      item.setProperty('IsPlayable', 'true')
      item.setProperty('Fanart_Image', FANART)
      items.append((PATH + '?vaata=%s' %  s.group(1), item))
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addDirectoryItems(HANDLE, items)
    xbmcplugin.endOfDirectory(HANDLE)
    
  def getMediaKey(self,saade):
    url = URL + 'vaata/' + saade
    buggalo.addExtraData('url', url)
    html = self.downloadUrl(url)
    
    if html:
      key = re.search('data">([^<]+).MXF</', html, re.DOTALL|re.IGNORECASE)
      if key:
        # NOTE: .mp4 works as well
        return key.group(1) + '.flv'
    else:
      raise ErrException(ADDON.getLocalizedString(202))

  def playStream(self,saade):
    url = 'rtmp://media.err.ee/arhiiv/%s' % self.getMediaKey(saade)
    buggalo.addExtraData('url', url)
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    
    item = xbmcgui.ListItem(saade, iconImage = ICON, path = url)
    playlist.add(url,item)
    xbmcplugin.setResolvedUrl(HANDLE, True, item)
    
  def displayError(self, message = 'n/a'):
    heading = buggalo.getRandomHeading()
    line1 = ADDON.getLocalizedString(200)
    line2 = ADDON.getLocalizedString(201)
    xbmcgui.Dialog().ok(heading, line1, line2, message)
    
if __name__ == '__main__':
  ADDON = xbmcaddon.Addon()
  PATH = sys.argv[0]
  HANDLE = int(sys.argv[1])
  PARAMS = urlparse.parse_qs(sys.argv[2][1:])
  
  ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
  FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')
  
  CACHE_PATH = xbmc.translatePath(ADDON.getAddonInfo("Profile"))
  if not os.path.exists(CACHE_PATH):
    os.makedirs(CACHE_PATH)
    

  buggalo.SUBMIT_URL = 'https://pilves.eu/exception/submit.php'
  
  ErrAddon = Err()
  try:
    if PARAMS.has_key('seeria') and PARAMS.has_key('saade'):
      ErrAddon.listSaade(PARAMS['seeria'][0], PARAMS['saade'][0])
    elif PARAMS.has_key('seeria'):
      ErrAddon.listSeries(PARAMS['seeria'][0])
    elif PARAMS.has_key('vaata'):
      ErrAddon.playStream(PARAMS['vaata'][0])
    else:
      ErrAddon.listErrCategory()
  except ErrException, ex:
    ErrAddon.displayError(str(ex))
  except Exception:
    buggalo.onExceptionRaised()
