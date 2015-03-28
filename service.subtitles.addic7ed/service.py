# -*- coding: utf-8 -*- 

import os
import sys
import xbmc
import urllib
import xbmcvfs
import xbmcaddon
import xbmcgui,xbmcplugin


import re,string, urllib, urllib2, socket,unicodedata
from BeautifulSoup import BeautifulSoup

__addon__ = xbmcaddon.Addon()
__author__     = __addon__.getAddonInfo('author')
__scriptid__   = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__    = __addon__.getAddonInfo('version')
__language__   = __addon__.getLocalizedString

__cwd__        = xbmc.translatePath( __addon__.getAddonInfo('path') ).decode("utf-8")
__profile__    = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) ).decode("utf-8")
__temp__       = xbmc.translatePath( os.path.join( __profile__, 'temp') ).decode("utf-8")

if not xbmcvfs.exists(__temp__):
  xbmcvfs.mkdirs(__temp__)

sys.path.append (__resource__)

def log(module, msg):
  xbmc.log((u"### [%s] - %s" % (module,msg,)).encode('utf-8'),level=xbmc.LOGDEBUG ) 

def normalizeString(str):
  return unicodedata.normalize(
         'NFKD', unicode(unicode(str, 'utf-8'))
         ).encode('ascii','ignore')
    
self_host = "http://www.addic7ed.com"
self_release_pattern = re.compile(" \nVersion (.+), ([0-9]+).([0-9])+ MBs")

def compare_columns(b,a):
    return cmp( a["sync"], b["sync"] ) or cmp( b["language_name"], a["language_name"] )
 
def get_url(url):
    req_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.A.B.C Safari/525.13',
    'Referer': 'http://www.addic7ed.com'}
    request = urllib2.Request(url, headers=req_headers)
    opener = urllib2.build_opener()
    response = opener.open(request)

    contents = response.read() 
    return contents    

def find_show_id(series):
    """Find a show id from the series

    Use this only if the series is not in the dict returned by :meth:`get_show_ids`

    :param string series: series of the episode
    :return: the show id, if any
    :rtype: int or None

    """
    params = {'search': series, 'Submit': 'Search'}
    log('Searching series %r', params)
    suggested_shows = get('/search.php', params).select('span.titulo > a[href^="/show/"]')
    if not suggested_shows:
        log('Series %r not found', series)
        return None
    return int(suggested_shows[0]['href'][6:])

def query_TvShow(name, season, episode, file_original_path, langs):
    sublinks = []
    name = name.lower().replace(" ", "_").replace("$#*!","shit").replace("'","") # need this for $#*! My Dad Says and That 70s show
    searchurl = "%s/serie/%s/%s/%s/addic7ed" %(self_host, name, season, episode)
    print searchurl
    socket.setdefaulttimeout(10)
    page = urllib2.urlopen(searchurl)
    content = page.read()
    content = content.replace("The safer, easier way", "The safer, easier way \" />")
    soup = BeautifulSoup(content)

    for subs in soup("td", {"class":"NewsTitle", "colspan" : "3"}):
      try:          
        subteams = str(subs).split('>Version ')[1].split(',')[0].replace("\n","")
        file_name = os.path.basename(file_original_path).lower()
        if (file_name.find(str(subteams.lower()))) > -1:
          hashed = True
        else:
          hashed = False
        langs_html = subs.findAllNext("td", {"class" : "language"})
        for lng in langs_html:
     
          fullLanguage = str(lng).split('class="language">')[1].split('<a href=')[0].replace("\n","")
          print fullLanguage
          try:
            lang = xbmc.convertLanguage(fullLanguage,xbmc.ISO_639_1)
          except:
            lang = ""       
          statusTD = lng.findNext("td")
          status = statusTD.find("b").string.strip()
          link = "%s%s"%(self_host,statusTD.findNext("td").find("a")["href"])
          if status == "Completed" and (lang in langs) :
            sublinks.append({'filename':"%s.S%.2dE%.2d-%s" %(name.replace("_", ".").title(),int(season), int(episode),subteams ),
                          'link':link,
                          'language_name':fullLanguage,
                          'language_id':lang,
                          'language_flag':lang,
                          'movie':"movie",
                          "ID":"subtitle_id",
                          "rating":"0",
                          "format":"srt",
                          "sync":hashed,
                          "hearing_imp":False})
      except:
        print "Error"
    
    return sublinks 
 
 
def get_params(string=""):
  param=[]
  if string == "":
    paramstring=sys.argv[2]
  else:
    paramstring=string 
  if len(paramstring)>=2:
    params=paramstring
    cleanedparams=params.replace('?','')
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
    pairsofparams=cleanedparams.split('&')
    param={}
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]
                                
  return param

params = get_params()

if params['action'] == 'search':
  log( __name__, "action 'search' called")
  item = {}
  item['temp']               = False
  item['rar']                = False
  item['year']               = xbmc.getInfoLabel("VideoPlayer.Year")                         # Year
  item['season']             = str(xbmc.getInfoLabel("VideoPlayer.Season"))                  # Season
  item['episode']            = str(xbmc.getInfoLabel("VideoPlayer.Episode"))                 # Episode
  item['tvshow']             = normalizeString(xbmc.getInfoLabel("VideoPlayer.TVshowtitle"))  # Show
  item['title']              = normalizeString(xbmc.getInfoLabel("VideoPlayer.OriginalTitle"))# try to get original title
  item['file_original_path'] = urllib.unquote(xbmc.Player().getPlayingFile().decode('utf-8'))# Full path of a playing file
  item['2let_language']      = []
  
  for lang in urllib.unquote(params['languages']).decode('utf-8').split(","):
    if lang == "Portuguese (Brazil)":
      lan = "pb"
    else:  
      lan = xbmc.convertLanguage(lang,xbmc.ISO_639_1)
#      if lan == "gre":
#        lan = "ell"

    item['2let_language'].append(lan)
  
  if item['title'] == "":
    log( __name__, "VideoPlayer.OriginalTitle not found")
    item['title']  = normalizeString(xbmc.getInfoLabel("VideoPlayer.Title"))      # no original title, get just Title
    
  if item['episode'].lower().find("s") > -1:                                      # Check if season is "Special"
    item['season'] = "0"                                                          #
    item['episode'] = item['episode'][-1:]
  
  if ( item['file_original_path'].find("http") > -1 ):
    item['temp'] = True

  elif ( item['file_original_path'].find("rar://") > -1 ):
    item['rar']  = True
    item['file_original_path'] = os.path.dirname(item['file_original_path'][6:])

  elif ( item['file_original_path'].find("stack://") > -1 ):
    stackPath = item['file_original_path'].split(" , ")
    item['file_original_path'] = stackPath[0][8:]
  
  subtitles_list = []
  log( __name__ ,"Title = %s" %  item['title'])
  if len(item['tvshow']) > 0: # TV Shows
      subtitles_list = query_TvShow(item['tvshow'], item['season'], item['episode'],item['file_original_path'], item['2let_language'])
      if( len ( subtitles_list ) > 0 ):
          subtitles_list = sorted(subtitles_list, compare_columns)

      if subtitles_list:
        for it in subtitles_list:
          listitem = xbmcgui.ListItem(label=it["language_name"],
                                      label2=it["filename"],
                                      iconImage=it["rating"],
                                      thumbnailImage=it["language_flag"]
                                      )
          if it["sync"]:
            listitem.setProperty( "sync", "true" )
          else:
            listitem.setProperty( "sync", "false" )
        
          if it.get("hearing_imp", False):
            listitem.setProperty( "hearing_imp", "true" )
          else:
            listitem.setProperty( "hearing_imp", "false" )
          
          url = "plugin://%s/?action=download&link=%s" % (__scriptid__, it["link"])
          
          xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False)


elif params['action'] == 'download':

  url = params["link"]
  file = os.path.join(__temp__, "adic7ed.srt")

  f = get_url(url)

  local_file_handle = open(file, "w" + "b")
  local_file_handle.write(f)
  local_file_handle.close() 

  listitem = xbmcgui.ListItem(label=file)
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=file,listitem=listitem,isFolder=False)
  
xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
  
  
  
  
  
  
  
  
    
