import re, html, nltk, os, argparse, time
from w3lib.html import replace_entities
from nltk.stem.porter import PorterStemmer
from math import log
from math import sqrt
from collections import Counter

# global variable
idx_table = {}
docu_table = {}
stop_words = set()

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
	if not validDate(month, day, year): # check date
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
	p_file_extension = re.compile(r'([^\\\/:*?\"<>|\s]+)\.(aif|cda|mid|midi|mp3|mpa|ogg|wav|wma|wpl|7z|arj|deb|pkg|rar|rpm|tar\.gz|z|zip|bin|dmg|iso|toast|vcd|csv|dat|db|dbf|log|mdb|sav|sql|tar|xml|apk|bat|bin|cgi|pl|com|exe|gadget|jar|py|wsf|fnt|fon|otf|ttf|ai|bmp|gif|ico|jpeg|jpg|png|ps|psd|svg|tif|tiff|asp|aspx|cer|cfm|css|htm|html|js|jsp|part|php|rss|xhtml|key|odp|pps|ppt|pptx|class|cpp|cs|h|java|sh|swift|vb|ods|xlr|xls|xlsx|bak|cab|cfg|cpl|cur|dll|dmp|drv|icns|ico|ini|lnk|msi|sys|tmp|3g2|3gp|avi|flv|h264|m4v|mkv|mov|mp4|mpg|mpeg|rm|swf|vob|wmv|doc|docx|odt|pdf|rtf|tex|txt|wks|wps|wpd)', re.I)
	p_prefix = re.compile(r'\b(a|an|ante|anti|auto|circum|co|com|con|contra|contro|de|dis|en|em|ex|extra|fore|hetero|homo|homeo|hyper|il|im|in|ir|inter|intra|intro|macro|micro|mid|mis|mono|non|omni|over|post|pre|pro|re|semi|sub|super|sym|syn|trans|tri|un|under|uni)-([a-z])+\b', re.I)
	p_hyphen = re.compile(r'\b(\w+-)+\w+\b')

	# create a porter stemmer
	stemmer = PorterStemmer()
	# convert all character references (e.g. &gt;, &#62;, &x3e;) to unicode
	query = replace_entities(query)
	query = html.unescape(query)
	# some queries have '/', need to be handled specifically
	query = query.replace('/', ' / ')
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
	# remove term not in idx_table (value will be 0 for all retrieval)
	query = [x for x in query if x in idx_table]
	return query

def df(term):
	return len(idx_table[term])

def idf(term):
	return log(len(docu_table) / df(term), 10)

def cosineSimilarity(query, docno, query_counter):
	c_dividend = 0 # dividend in formula
	c_divisor_d = 0 # document divisor in formula
	c_divisor_w = 0 # query divisor in formula
	for term in query:
		w = query_counter[term] * idf(term)
		d = docu_table[docno][term] * idf(term)
		c_dividend += w * d
		c_divisor_w += w ** 2
	for term in docu_table[docno]:
		d = docu_table[docno][term] * idf(term)
		c_divisor_d += d ** 2
	return c_dividend / sqrt(c_divisor_d * c_divisor_w)

def bm25Similarity(query, docno, query_counter, totaldl):
	k1 = 1.2
	k2 = 500
	b = 0.75
	N = len(docu_table)
	D = sum(docu_table[docno].values())
	avgdl = totaldl / len(docu_table)
	res = 0
	for term in query:
		n = len(idx_table[term])
		tf = idx_table[term][docno]
		p1 = (k1 + 1) * tf / (tf + k1 * (1 - b + b * D / avgdl))
		p2 = (k2 + 1) * query_counter[term] / (k2 + query_counter[term])
		res += idf(term) * p1 * p2
	return res

def lmSimilarity(query, docno, query_counter, totaldl):
	D = sum(docu_table[docno].values())
	avgdl = totaldl / len(docu_table)
	res = 0
	for term in query:
		tf = idx_table[term][docno]
		tfC = sum(idx_table[term].values())
		res += log(((tf + avgdl * tfC / totaldl) / (D + avgdl)), 10)
	return res

def relevanceRanking(query, args, totaldl):
	result = Counter()
	# find relevant doc containing at least one query term
	relevant_doc = set()
	for term in query:
		for docno in idx_table[term]:
			relevant_doc.add(docno)
	# build query counter to calculate tf in query
	query_counter = Counter()
	for term in query:
		query_counter[term] += 1
	# calculate relevance
	for docno in relevant_doc:
		if args.retrieval_model == 'cosine':
			result[docno] = cosineSimilarity(query, docno, query_counter)
		elif args.retrieval_model == 'bm25':
			result[docno] = bm25Similarity(query, docno, query_counter, totaldl)
		elif args.retrieval_model == 'lm':
			result[docno] = lmSimilarity(query, docno, query_counter, totaldl)
	return result.most_common(100)

def parseSTPI(line, idx):
	parts = line.split()
	# term, docno, term frequency, term positions
	return [(parts[0], parts[1]), int(parts[2]), parts[3:], idx]

def parsePI(line, idx):
	parts = line.split()
	if parts[2].startswith('FR'):
		return [(parts[0]+' '+parts[1], parts[2]), int(parts[3]), idx]
	else:
		return [(parts[0]+' '+parts[1]+' '+parts[2], parts[3]), int(parts[4]), idx]

def parseCommand():
	parser = argparse.ArgumentParser(description='Static query processing. Runs the specified retrieval model on the specified index type. Accepts 5 arguments.')
	parser.add_argument('index_path', help='The path of index files.')
	parser.add_argument('query_file', help='The path and name of query file.')
	parser.add_argument('retrieval_model', choices=['cosine', 'bm25', 'lm'], help='retrieval model: cosine / bm25 / lm')
	parser.add_argument('index_type', choices=['single', 'stem'], help='[single / stem] for single term index / stem index')
	parser.add_argument('output_path', help='The path of output file (Retrieval result).')
	args = parser.parse_args()
	if args.index_path[0] == '/':
		args.index_path = '.' + args.index_path
	if args.index_path[-1] != '/':
		args.index_path += '/'
	if args.output_path[0] == '/':
		args.output_path = '.' + args.output_path
	if args.output_path[-1] != '/':
		args.output_path += '/'
	return args

def loadIndexTables(args):
	# load stop word set
	f = open('stops.txt', 'r')
	for line in f:
		stop_words.add(line.strip())
	f.close()
	totaldl = 0
	# load index table
	if args.index_type == 'single':
		f = open(args.index_path+'single_term_idx.txt', 'r')
	elif args.index_type == 'stem':
		f = open(args.index_path+'stem_idx.txt', 'r')
	for line in f:
		parts = line.split()
		if not parts[0] in idx_table:
			idx_table[parts[0]] = Counter()
		if not parts[1] in docu_table:
			docu_table[parts[1]] = Counter()
		# term, docno, term frequency
		idx_table[parts[0]][parts[1]] = int(parts[2])
		docu_table[parts[1]][parts[0]] = int(parts[2])
		totaldl += int(parts[2])
	f.close()
	return totaldl

if __name__ == '__main__':
	t1 = time.time()
	args = parseCommand()
	totaldl = loadIndexTables(args)
	# open input query file and output retrieval file
	input_file = open(args.query_file, 'r')
	# create output directory if not exists
	if not os.path.exists(args.output_path):
		os.makedirs(args.output_path)
	output_file = open(args.output_path+args.retrieval_model+'-'+args.index_type+'.txt', 'w')

	rank = 0
	line = input_file.readline()
	while line:
		if line.startswith('<num>'):
			num = line.split()[-1]
		elif line.startswith('<title>'):
			query = ' '.join(line.split()[2:])
			line = input_file.readline().strip()
			if line:
				query += ' ' + line
			query = queryPreprocessing(query, args)
			result = relevanceRanking(query, args, totaldl)
			for (docno, weight) in result:
				output_file.write(num+' 0 '+docno+' '+str(rank)+' '+str(weight)+' '+args.retrieval_model+'\n')
				rank += 1
		line = input_file.readline()
	input_file.close()
	output_file.close()

	t3 = time.time()
	print('Total time:', round((t3 - t1), 2), 's')