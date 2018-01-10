import urllib2

DOMAIN = "http://online-life.club"

print("Online-life")

def httpToString(url):
    response = urllib2.urlopen(DOMAIN)
    html = response.read();
    return html

page = httpToString(DOMAIN)
print(page)

#encoding = response.headers.get_content_charset('utf-8')
#decoded_html = html_response.decode(encoding)
#print(decoded_html)

