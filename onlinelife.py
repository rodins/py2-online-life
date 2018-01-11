#!/usr/bin/python
# -*- coding: UTF-8 -*-

import urllib2

DOMAIN = "http://online-life.club"
DOMAIN_NO_SUFFIX = "www.online-life."

print("Online-life")

class Result:
	title = ""
	href = ""

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
        print("JS: " + js)
    except:
		print("Network problem")
    
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
	resultHttpToString(result_id)
	
		
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
			    processResult(result)
		except ValueError:
			print("Wrong input")
	    	

#page = httpToString(DOMAIN)
#stringToFile(page)
page = fileToString()
#print(page)
results = resultsParser(page)

selectResult(results)



