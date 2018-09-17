# import re, nltk, html
# from w3lib.html import replace_entities
# from nltk.stem.porter import PorterStemmer

def dotAcronym(match):
	temp = match.group()
	temp = temp.replace('.', '')
	return temp

def digitAlpha(match):
	num, word = match.group(1), match.group(2)
	temp = num + word
	if len(word) >= 3 and not word in stop_words:
		temp += ' ' + word
	return temp

def alphaDigit(match):
	word, num = match.group(1), match.group(2)
	temp = word + num
	if len(word) >= 3 and not word in stop_words:
		temp += ' ' + word
	return temp

def prefixReplace(match):
	prefix, stem = match.group(1), match.group(2)
	temp = prefix + stem
	if not stem in stop_words:
		temp += ' ' + stem
	return temp

def hyphenReplace(match):
	temp = match.group()
	li = temp.split('-')
	temp = temp.replace('-', '')
	for item in li:
		if not item in stop_words:
			temp += ' ' + item
	return temp

def validDate(month, day, year):
	if month <= 0 or month > 12 or year > 2018 or year < 0 or day <= 0:
		return False
	if (month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12) and day > 31:
		return False
	if month == 2 and day > 29:
		return False
	if (month == 4 or month == 6 or month == 9 or month == 11) and day > 30:
		return False
	return True

def dateReplace(match):
	date = match.group()
	# date convert to number
	if date[0] >= '0' and date[0] <= '9':
		d = re.split(r'[-/]', date)
		month, day, year = int(d[0]), int(d[1]), int(d[2])
	else:
		d = date.split()
		t_m, t_d, year = d[0], d[1], int(d[2])
		# convert jan(uary) feb(urary) into number 1, 2 ...
		if t_m[0] == 'j':
			if t_m[1] == 'a':
				month = 1
			elif t_m[2] == 'n':
				month = 6
			else:
				month = 7
		elif t_m[0] == 'f':
			month = 2
		elif t_m[0] == 'm':
			if t_m[2] == 'r':
				month = 3
			else:
				month = 5
		elif t_m[0] == 'a':
			if t_m[1] == 'p':
				month = 4
			else:
				month = 8
		elif t_m[0] == 's':
			month = 9
		elif t_m[0] == 'o':
			month = 10
		elif t_m[0] == 'n':
			month = 11
		else:
			month = 12
		# convert '10' or '1' into number
		if t_d[1] >= '0' and t_d[1] <= '9':
			day = 10 * int(t_d[0]) + int(t_d[1])
		else:
			day = int(t_d[0])
	# end of date conversion into number
	# check date
	if not validDate(month, day, year):
		return '' # remove this date
	if year < 100:
		if year <= 18:
			year += 2000
		else:
			year += 1900
	s_month = str(month)
	if month < 10:
		s_month = '0' + s_month
	s_day = str(day)
	if day < 10:
		s_day = '0' + s_day
	return s_month+'/'+s_day+'/'+str(year)

def queryPreprocessing(query, args):
	# regular expressions
	p_tag_comment = re.compile(r'(<.*?>|<!--.*-->)')
	p_alpha_digit = re.compile(r'\b([a-z]+)-([0-9]+)\b', re.I)
	p_digit_alpha = re.compile(r'\b([0-9]+)-([a-z]+)\b', re.I)
	p_dot_acronym = re.compile(r'\b([a-z]+\.)+[a-z]+(\.|\b)', re.I)
	p_date = re.compile(r"""\b
		([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})
		|([0-9]{1,2}-[0-9]{1,2}-[0-9]{2,4})
		|(((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.]?
		|January|February|March|April|May|June|July|August
		|September|October|November|December)
		\ [0-9]{1,2}(st|nd|rd|th)?,\ [0-9]{2,4})
	 	\b""", re.VERBOSE | re.I)
	p_docno = re.compile(r'(?:<DOCNO>\s*)(.+)(?:\s*</DOCNO>)', re.I)
	p_num1 = re.compile(r',([0-9]{3})')
	p_num2 = re.compile(r'\b(\d+)[.]0+\b')
	# p_email = re.compile(r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b', re.I)
	# p_url = re.compile(r'\b(https?|ftp)://w{3}[a-z0-9_/.-]{2,}', re.I)
	p_file_extension = re.compile(r'([^\\\/:*?\"<>|\s]+)\.(aif|cda|mid|midi|mp3|mpa|ogg|wav|wma|wpl|7z|arj|deb|pkg|rar|rpm|tar\.gz|z|zip|bin|dmg|iso|toast|vcd|csv|dat|db|dbf|log|mdb|sav|sql|tar|xml|apk|bat|bin|cgi|pl|com|exe|gadget|jar|py|wsf|fnt|fon|otf|ttf|ai|bmp|gif|ico|jpeg|jpg|png|ps|psd|svg|tif|tiff|asp|aspx|cer|cfm|css|htm|html|js|jsp|part|php|rss|xhtml|key|odp|pps|ppt|pptx|class|cpp|cs|h|java|sh|swift|vb|ods|xlr|xls|xlsx|bak|cab|cfg|cpl|cur|dll|dmp|drv|icns|ico|ini|lnk|msi|sys|tmp|3g2|3gp|avi|flv|h264|m4v|mkv|mov|mp4|mpg|mpeg|rm|swf|vob|wmv|doc|docx|odt|pdf|rtf|tex|txt|wks|wps|wpd)', re.I)
	p_prefix = re.compile(r'\b(a|an|ante|anti|auto|circum|co|com|con|contra|contro|de|dis|en|em|ex|extra|fore|hetero|homo|homeo|hyper|il|im|in|ir|inter|intra|intro|macro|micro|mid|mis|mono|non|omni|over|post|pre|pro|re|semi|sub|super|sym|syn|trans|tri|un|under|uni)-([a-z])+\b', re.I)
	p_hyphen = re.compile(r'\b(\w+-)+\w+\b')
	# p_ip = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\b')

	# create a porter stemmer
	stemmer = PorterStemmer() 
	# convert all character references (e.g. &gt;, &#62;, &x3e;) to unicode
	query = replace_entities(query)
	query = html.unescape(query)
	# convert to lower case
	query = query.lower()
	# expand file extension
	query = p_file_extension.sub(r'\g<1>\g<2> \g<2>', query)
	# ph.D. -> phd
	query = p_dot_acronym.sub(dotAcronym, query)
	# convert date to mm/dd/yyyy format or remove it if invalid
	query = p_date.sub(dateReplace, query)
	# digit format
	query = p_num1.sub(r'\g<1>', query) # remove ',' in 1,000
	query = p_num2.sub(r'\g<1>', query) # remove '.00' in 1.00
	# expand digit-alpha format
	query = p_digit_alpha.sub(digitAlpha, query)
	# expand alpha-digit format
	query = p_alpha_digit.sub(alphaDigit, query)
	# expand stem with hyphen prefix
	query = p_prefix.sub(prefixReplace, query)
	# expand hyphenated word
	query = p_hyphen.sub(hyphenReplace, query)
	# tokenize query
	query = nltk.word_tokenize(query)

	# apply Porter Stemmer
	if args.index_type == 'stem':
		query = [stemmer.stem(word) for word in query]
	return query

def df(term):
	return len(idx_table[term])

def idf(term):
	return math.log(len(docu_table) / df(term), 10)

def cosineSimilarity(query, docno):
	# build query counter to calculate tf in query
	query_counter = Counter()
	for term in query:
		query_counter[term] += 1
	# use improved weight measure for query term
	# precalculate divisor in query
	q_divisor = 0
	for term in query:
		q_divisor += ((math.log(query_counter[term], 10) + 1) * idf(term)) ** 2
	# calculate cosine similarity
	c_dividend = 0 # dividend in formula
	c_divisor_d = 0 # document divisor in formula
	c_divisor_w = 0 # query divisor in formula
	for term in query:
		w = (log(query_counter[term], 10) + 1) * idf(term) / q_divisor
		d = docu_table[docno][term] * idf(term)
		c_dividend += w * d
		c_divisor_d += d ** 2
		c_divisor_w += w ** 2
	return c_dividend / math.sqrt(c_divisor_d * c_divisor_w)

class Temp():
	def __init__(self, index_type):
		self.index_type = index_type

# stop_words = set()
# f = open('stops.txt', 'r')
# for line in f:
# 	stop_words.add(line.strip())
# f.close()
# args = Temp('stem')
# # args.index_type = 'single'
# while 1:
# 	query = input('query: ')
# 	print(queryPreprocessing(query, args))
# query = 'a.pdf'
# query = p_file_extension.sub(r'\g<1>.\g<2> \g<2>', query)
# print(query)

# line = '<title> Topic: Herbal Food Supplements/Natural Health \n'
# query = ' '.join(line.split()[2:])
# line = 'Care Products\n'.strip()

# if line:
# 	query += ' ' + line
# query = query.replace('/', ' / ') # some queries have /
# print(query)

def posMatch(docno, phrase, pos):
	if not phrase:
		return 1
	i = 0
	positions = pos_idx[phrase[0]][docno]
	while (i < len(positions) and positions[i] <= pos):
		i += 1
	if i == len(positions):
		return 0
	else:
		count = 0
		while i < len(positions) and positions[i] <= pos + 3:
			count += posMatch(docno, phrase[1:], positions[i])
			i += 1
		return count

from collections import Counter

pos_idx = {}
pos_idx['a'] = {}
pos_idx['b'] = {}
pos_idx['c'] = {}
pos_idx['d'] = {}
pos_idx['a']['d1'] = [0, 3, 10]
pos_idx['b']['d1'] = [4, 5, 12]
pos_idx['c']['d1'] = [6, 7, 14]
query = ['a', 'b', 'c', 'd']
phrase_idx = {}
relevant_doc = set()
# check bigram
for i in range(len(query) - 1):
	bigram = [query[i], query[i + 1]]
	for docno in set(pos_idx[bigram[0]]).intersection(pos_idx[bigram[1]]):
		for pos in pos_idx[bigram[0]][docno]:
			tf = posMatch(docno, bigram[1], pos)
			if tf > 0:
				phrase = ' '.join(bigram)
				if not phrase in phrase_idx:
					phrase_idx[phrase] = Counter()
				phrase_idx[phrase][docno] += tf
				relevant_doc.add(docno)
# check trigram
for i in range(len(query) - 2):
	trigram = [query[i], query[i + 1], query[i + 2]]
	for docno in set(pos_idx[trigram[0]]).intersection(pos_idx[trigram[1]]).intersection(pos_idx[trigram[2]]):
		for pos in pos_idx[trigram[0]][docno]:
			tf = posMatch(docno, trigram[1], pos)
			if tf > 0:
				phrase = ' '.join(trigram)
				if not phrase in phrase_idx:
					phrase_idx[phrase] = Counter()
				phrase_idx[phrase][docno] += tf
print(phrase_idx)