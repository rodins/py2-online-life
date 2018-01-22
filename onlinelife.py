#!/usr/bin/python
# -*- coding: UTF-8 -*-

import urllib
import urllib2

DOMAIN = "http://online-life.club"
WDOMAIN = "http://www.online-life.club"
DOMAIN_NO_SUFFIX = "www.online-life."

print("Online-life")

class Result:
	title = ""
	href = ""
	
class PlayItem:
	comment = ""
	file = ""
	download = ""
	
class Playlist:
	comment = ""
	items = []
	
class ResultInfo:
	title = ""
	country = ""
	year = ""
	items = []
	
class Category:
	result = None
	results = []

def httpToString(url):
	try:
	    response = urllib2.urlopen(url)
	    #TODO: parse one item at the time
	    html = response.read()
	    return html
	except Exception as ex:
		print("Network problem", ex)
		return ""
    
def resultHttpToString(result_id):
    url = "http://dterod.com/js.php?id=" + result_id;
    referer = "http://dterod.com/player.php?newsid=" + result_id;
    headers = {'Referer': referer}
    try:
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)
        js = response.read()
        js = js.decode('cp1251')
        return js
    except:
		print("Network problem")
		return ""

def infoHttpToString(url):
	print("Getting info...")
	try:
		response = urllib2.urlopen(url)
		resultInfo = ResultInfo()
		for line in response:
			utf_line = line.decode('cp1251')
			#print("LINE_START" + utf_line + "LINE_END")
			
			if resultInfo.year == "":
				resultInfo.year = parseSimpleInfo(utf_line, u"Год: ")
			elif resultInfo.country == "":
				resultInfo.country = parseSimpleInfo(utf_line, u"Страна: ")
			elif len(resultInfo.items) == 0:
				resultInfo.items = parseActors(utf_line, u"Режиссер:", u" (режиссер)")
			else:
				len_prev = len(resultInfo.items)
				resultInfo.items += parseActors(utf_line, u"В ролях:")
				if len_prev < len(resultInfo.items):
					return resultInfo
				
	except Exception as ex:
		print("Network problem", ex)
		
def parseActors(line, query, director = ""):
	items = []
	actors_begin = line.find(query)
	actors_end = line.find("\n")
	if actors_begin != -1 and actors_end != -1:
		actors = line[actors_begin: actors_end]
		#print("Actors: " + actors)
		
		begin = "<a href"
		end = "</a>"
		anchor_begin = actors.find(begin)
		anchor_end = actors.find(end)
		while anchor_begin != -1 and anchor_end != -1:
			item = Result()
			anchor = actors[anchor_begin: anchor_end]
			#print("Anchor: " + anchor)
			
			title_begin = anchor.find(">")
			if title_begin != -1:
				item.title = anchor[title_begin+1:] + director
				#print("Title: " + item.title)
				
				href_begin = anchor.find("href=")
				href_end = anchor.find(">", href_begin)
				if href_begin != -1 and href_end != -1:
					item.href = anchor[href_begin+6: href_end-1]
					#print("Href: " + item.href)
					items.append(item)
			
			anchor_begin = actors.find(begin, anchor_end)
			anchor_end = actors.find(end, anchor_begin)
	return items
	
def parseSimpleInfo(line, query):
	info_begin = line.find(query)
	info_end = line.find("\n", info_begin)
	if info_begin != -1 and info_end != -1:
		return line[info_begin: info_end]
	else:
		return ""

def categoriesToItems():
	try:
		begin_found = False
		drop_found = False
		is_drop_first = False
		
		items = []
		
		response = urllib2.urlopen(DOMAIN)
		
		#response = open("Home.html", "r")
		
		for line in response:
			if line.find("<div class=\"nav\">") != -1:
				begin_found = True
				main = Category()
				mainCategoryItem = Result()
				mainCategoryItem.title = "Главная"
				mainCategoryItem.href = DOMAIN
				main.result = mainCategoryItem
				items.append(main)
			
			if begin_found:
				# Find new, popular, best
				pull_right_begin = line.find("li class=\"pull-right")
				pull_right_end = line.find("</li>", pull_right_begin+1)
				if pull_right_begin != -1 and pull_right_end != -1:
				    pull_right = line[pull_right_begin: pull_right_end]
				    result = parseAnchor(pull_right)
				    main.results.append(result)
				    continue
				
				trailer_begin = line.find("<li class=\"nodrop\" ")
				trailer_end = line.find("</a>", trailer_begin+1)
				if trailer_begin != -1 and trailer_end != -1:
					trailer = line[trailer_begin: trailer_end+4]
					result = parseAnchor(trailer)
					main.results.append(result)
					continue
				
				# Find drop item
				if line.find("<li class=\"drop\">") != -1:
					drop_found = True
					is_drop_first = True
					
				if drop_found:
					result = parseAnchor(line)
					if result != None:
						if is_drop_first:
							categoryItem = result
							results = []
							is_drop_first = False
						else:
							results.append(result)	
					
				if line.find("</ul>") != -1 and drop_found:
					drop_found = False
					category = Category()
					category.result = categoryItem
					category.results = results
					items.append(category)
								
			if line.find("</div>") != -1 and begin_found:
				begin_found = False
				response.close()
				return items
				
	except Exception as ex:
		print("Network problem", ex)
		
def parseAnchor(line):
	anchor_begin = line.find("<a href=")
	anchor_end = line.find("</a>")
	if anchor_begin != -1 and anchor_end != -1:
		anchor = line[anchor_begin:anchor_end]
		href_begin = anchor.find("\"")
		href_end = anchor.find("\"", href_begin+1)
		title_begin = anchor.find(">")
		href = anchor[href_begin+1: href_end]
		title = anchor[title_begin+1:]
		result = Result()
		result.title = title.decode('cp1251')
		if href.find(WDOMAIN) != -1:
			result.href = href
		else:
			result.href = WDOMAIN + href
		return result
		
def playlistParser(json):
	items = []
	item_start = json.find("{")
	item_end = json.find("}", item_start+1)
	while item_start != -1 and item_end != -1:
		item = json[item_start: item_end]
		play_item = playItemParser(item)
		items.append(play_item)
		
		item_start = json.find("{", item_end)
		item_end = json.find("}", item_start)
	return items
		
def playlistsParser(json):
	playlists = []
	begin = "\"comment\""
	end = "]"
	playlist_begin = json.find(begin)
	playlist_end = json.find(end, playlist_begin)
	while playlist_begin != -1 and playlist_end != -1:
		playlist = json[playlist_begin: playlist_end]
		
		comment_begin = playlist.find(begin)
		comment_end = playlist.find("[", comment_begin+11)
		if comment_begin != -1 and comment_end != -1:
			comment = playlist[comment_begin+11: comment_end]
			comment_new_end = comment.find("\",")
			if comment_new_end != -1:
				comment = playlist[comment_begin+11: comment_new_end]
	
			items = playlist[comment_end+1:]		
			playlist = Playlist()
			playlist.comment = comment
			playlist.items = playlistParser(items)
			if comment != "":
				playlists.append(playlist)
			else:
				return playlist.items
			
		playlist_begin = json.find(begin, playlist_end+2)
		playlist_end = json.find(end, playlist_begin+1)
	return playlists

def playlistLinkParser(js):
	link_begin = js.find("pl:")
	link_end = js.find("\"", link_begin+4)
	if link_begin != -1 and link_end != -1:
		link = js[link_begin+4: link_end]
		return link
	return ""
	
def playItemParser(js):
	play_item = PlayItem()
	
	# Search for file
	file_begin = js.find("\"file\"")
	file_end = js.find("\"", file_begin+10)
	if file_begin != -1 and file_end != -1:
		play_item.file = js[file_begin+8: file_end]
	
	# Search for download
	download_begin = js.find("\"download\"")
	download_end = js.find("\"", download_begin+12)
	if download_begin != -1 and download_end != -1:
		play_item.download = js[download_begin+12: download_end]
		
	# Search for comment
	comment_begin = js.find("\"comment\"")
	comment_end = js.find("\"", comment_begin+11)
	if comment_begin != -1 and comment_end != -1:
		play_item.comment = js[comment_begin+11: comment_end]
		
	return play_item	
    
def getHrefId(href):
	id_begin = href.find(DOMAIN_NO_SUFFIX)
	# id_begin detection make suffix independent
	if id_begin != -1:
		id_begin = href.find("/", id_begin+1)
		
	id_end = href.find("-", id_begin)
	if id_begin != -1 and id_end != -1:
		id_str = href[id_begin+1: id_end]
		return id_str
	
	
def resultsParser(page):
	results = []
	begin = "<div class=\"custom-poster\""
	end = "</a>"
	div_begin = page.find(begin)
	div_end = page.find(end, div_begin)
	while div_begin != -1 and div_end != -1:
		div = page[div_begin: div_end]
		
		title_begin = div.find("/>")
		if title_begin != -1:
			title = div[title_begin+2: div_end]
			# Delete title new line
			title_new_line = title.find('\n')
			if title_new_line != -1:
				title = title[:title_new_line]
			
			# convert from cp1251 to utf8
			title = title.decode('cp1251')
			
			href_begin = div.find("href=")
			href_end = div.find(".html", href_begin+1)
			if href_begin != -1 and href_end != -1:
				href = div[href_begin+6: href_end+5]
                result = Result()
                result.title = title
                result.href = href
                results.append(result) 
                
				#TODO: detect poster image
		
		div_begin = page.find(begin, div_end)
		div_end = page.find(end, div_begin)
	
	return results	

def stringToFile(page):
	print("Saving...")
	with open("Home.html", "w") as f:
		f.write(page)

def fileToString():
    with open("Home.html", "r") as f:
		page = f.read()
		return page
		
def processPlayItem(play_item):
	print(play_item.comment)
	print("Play and download links found")
	print(play_item.file)
	print(play_item.download)
	
	# TODO: start mplayer of wget
	raw_input("Press ENTER to continue...")
		
def processLinks(result):
	result_id = getHrefId(result.href)
	js = resultHttpToString(result_id)
	# Probing for playlist link
	playlist_link = playlistLinkParser(js)
	if playlist_link != "":
		json = httpToString(playlist_link)
		if json != "":
			playlists = playlistsParser(json)
			if len(playlists) > 0:
				selectPlaylists(playlists)
			else:
				items = playlistParser(json)
				selectPlaylist(items)
	else:
		# Probing for play item
		play_item = playItemParser(js)
		if play_item.file != "":
			processPlayItem(play_item)
		else:
			# TODO: trailers detection
			print("Nothing found")

def processInfo(result):
	resultInfo = infoHttpToString(result.href)
	if resultInfo != None:
		resultInfo.title = result.title
		selectActor(resultInfo)
	raw_input("Press ENTER to continue...")
	
def processActorOrCategory(href):
	page = httpToString(href)
	results = resultsParser(page)
	selectResult(results)
	
def selectActor(resultInfo):
	while True:
		print(resultInfo.title)
		print(resultInfo.country)
		print(resultInfo.year)
		print("Actors:")
		for item in resultInfo.items:
			print("%d) %s" % (resultInfo.items.index(item)+1, item.title))
		ans = raw_input("Select item (q - exit): ")
		if ans == "q":
			return
		try:
			index = int(ans) - 1
			if index >= 0 and index < len(resultInfo.items):
				print("Processing actor: " + resultInfo.items[index].title)
				processActorOrCategory(resultInfo.items[index].href)
		except Exception as ex:
			print("Wrong input", ex)
		
def selectPlaylist(items):
	while True:
		for play_item in items:
			print("%d) %s" % (items.index(play_item)+1, play_item.comment))
		ans = raw_input("Select item (q - quit): ")
		if ans == "q":
			return
		try:
			index = int(ans)
			if index > 0 and index <= len(items):
				processPlayItem(items[index-1])
		except ValueError:
			print("Wrong playlist input")
	
def selectPlaylists(playlists):
	while True:
		for playlist in playlists:
			print("%d) %s" % (playlists.index(playlist)+1, playlist.comment))
		ans = raw_input("Select item (q - quit): ")
		if ans == "q":
			return
		try:
			index = int(ans)
			if index > 0 and index <= len(playlists):
				selectPlaylist(playlists[index-1].items)
		except Exception as ex:
			print("Wrong playlists input", ex)
				
def selectResult(results):
    while True:
		for result in results:
			print("%d) %s" % (results.index(result)+1, result.title))	
		ans = raw_input("Select number (q - exit): ")
		if ans == 'q':
			break
		try:
		    ans = int(ans)
		    if ans > 0 and ans <= len(results):
			    index = ans - 1
			    print("Selected: %s" % results[index].title)
			    ans = raw_input("Select mode (l - links, i - info): ")
			    if ans == "i":
					processInfo(results[index])
			    if ans == "l":
					processLinks(results[index])
		except ValueError as ex:
			print("Wrong results input", ex)
	    	
def selectSubcategory(items):
	while True:
		for result in items:
			print("%d) %s" % (items.index(result)+1, result.title))
		ans = raw_input("Select number (q - exit): ")
		if ans == 'q':
			break
		try:
			ans = int(ans)
			if ans > 0 and ans <= len(items):
				index = ans-1
				print("Selected: " + items[index].title)
				processActorOrCategory(items[index].href)
		except ValueError as ex:
			print("Wrong subcategory input", ex)
			
	    	
def selectCategory(items):
	while True:
		for category in items:
			print("%d) %s" % (items.index(category)+1, category.result.title))
		ans = raw_input("Select number (q - exit): ")
		if ans == 'q':
			break
		try:
			ans = int(ans)
			if ans > 0 and ans <= len(items):
				index = ans-1
				category = items[index]
				print("Selected: " + category.result.title)
				ans = raw_input("Select mode: r -results, s - subcategories, q - exit: ")
				if ans == 'r':
					processActorOrCategory(category.result.href)
				elif ans == 's':
					selectSubcategory(category.results)
				elif ans == 'q':
					break
		except ValueError as ex:
			print("Wrong categories input", ex)

def searchLoop():
	categories = []
	while True:
		ans = raw_input("Enter search query (c - categories, q - exit): ")
		if ans == 'c':
			if len(categories) == 0:
				categories = categoriesToItems()
				selectCategory(categories)
		elif ans == 'q':
			break
		else:
			query = ans.strip()
			cpQuery = query.decode('cp1251')
			print("Query: " + cpQuery)
			data = {}
			data['do'] = 'search'
			data['subaction'] = 'search'
			data['mode'] = 'simple'
			data['story'] = cpQuery
			url_values = urllib.urlencode(data)
			print(url_values)
			search_url = DOMAIN + "?" + url_values
			processActorOrCategory(search_url)				

#page = httpToString(DOMAIN)
#stringToFile(page)
#page = fileToString()
#print(page)
#results = resultsParser(page)
#selectResult(results)
#items = categoriesToItems()
#selectCategory(items)
searchLoop()
