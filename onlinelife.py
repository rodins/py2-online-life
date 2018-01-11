import urllib2

DOMAIN = "http://online-life.club"
DOMAIN_NO_SUFFIX = "www.online-life."

print("Online-life")

def httpToString(url):
    response = urllib2.urlopen(DOMAIN)
    # TODO read one line at a time, or read bytes
    html = response.read();
    return html
    
def getHrefId(href):
	id_begin = href.find(DOMAIN_NO_SUFFIX)
	# id_begin detection make suffix independent
	if id_begin != -1:
		id_begin = href.find("/", id_begin+1)
		
	id_end = href.find("-", id_begin)
	if id_begin != -1 and id_end != -1:
		id_str = href[id_begin+1: id_end]
		print("Id: " + id_str)
	
		
    
def resultsParser(page):
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
			
			#TODO: convert from cp1251 to utf8
			print("Title: " + title)
			
			href_begin = div.find("href=")
			href_end = div.find(".html", href_begin+1)
			if href_begin != -1 and href_end != -1:
				href = div[href_begin: href_end]
				print("Href: " + href)
				getHrefId(href)
				#TODO: detect poster image
		
		div_begin = page.find(begin, div_end)
		div_end = page.find(end, div_begin)

def stringToFile(page):
	print("Saving...")
	with open("Home.html", "w") as f:
		f.write(page)

def fileToString():
    with open("Home.html", "r") as f:
		page = f.read()
		return page


#page = httpToString(DOMAIN)
#stringToFile(page)
page = fileToString()
#print(page)
resultsParser(page)

#encoding = response.headers.get_content_charset('utf-8')
#decoded_html = html_response.decode(encoding)
#print(decoded_html)

