import urllib2

DOMAIN = "http://online-life.club"

print("Online-life")

def httpToString(url):
    response = urllib2.urlopen(DOMAIN)
    # TODO read one line at a time, or read bytes
    html = response.read();
    return html
    
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
			#TODO: convert from cp1251 to utf8
			print("Title: " + title)
			
			href_begin = div.find("href=")
			href_end = div.find(".html", href_begin+1)
			if href_begin != -1 and href_end != -1:
				href = div[href_begin: href_end]
				print("Href: " + href)
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

