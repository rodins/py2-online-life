#!/usr/bin/python
# -*- coding: UTF-8 -*-

import urllib2

DOMAIN = "http://online-life.club"
DOMAIN_NO_SUFFIX = "www.online-life."

print("Online-life")

class Result:
	title = ""
	href = ""
	
class PlayItem:
	comment = ""
	file = ""
	download = ""

def httpToString(url):
	try:
	    response = urllib2.urlopen(DOMAIN)
	    #TODO: parse one item at the time
	    html = response.read()
	    return html
	except:
		print("Network problem")
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
				href = div[href_begin+6: href_end]
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
		
def processResult(result):
	result_id = getHrefId(result.href)
	js = resultHttpToString(result_id)
	play_item = playItemParser(js)
	print("Comment: " + play_item.comment)
	playlist_link = playlistLinkParser(js)
	print("Playlist link: " + playlist_link)
	
		
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
			    processResult(results[index])
		except ValueError:
			print("Wrong input")
	    	

#page = httpToString(DOMAIN)
#stringToFile(page)
page = fileToString()
#print(page)
results = resultsParser(page)

selectResult(results)



