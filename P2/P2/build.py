import glob, re, html, nltk, os, heapq, argparse, sys, time, statistics, shutil
from w3lib.html import replace_entities
from collections import Counter
from collections import OrderedDict
from nltk.stem.porter import PorterStemmer

# global variable
size_limit = 1000
single_term_idx = Counter()
sti_fn = 0
single_term_pos_idx = OrderedDict()
stpi_fn = 0
stem_idx = Counter()
si_fn = 0
phrase_idx = Counter()
pi_fn = 0
stop_words = set()

# write single_term_idx/stem_idx/phrase_idx to file
def counterWriteToFile(var_name, fn, c):
	if len(c) == size_limit:
		f = open('tmp/'+var_name+'_'+str(fn)+'.txt', 'w', encoding='utf8')
		for key in sorted(c.keys()):
			f.write(' '.join(str(x) for x in key)+' '+str(c[key])+'\n')
		f.close()
		c.clear()
		fn += 1
	return fn

# write single_term_pos_idx to file
def orderedDictWriteToFile(var_name, fn, d):
	if len(d) == size_limit:
		f = open('tmp/'+var_name+'_'+str(fn)+'.txt', 'w', encoding='utf8')
		for key in d.keys():
			f.write(' '.join(str(x) for x in key)+' '+' '.join(str(x) for x in d[key])+'\n')
		f.close()
		d.clear()
		fn += 1
	return fn

def specialToken(line, regex, docno, sti_flag):
	global sti_fn
	li = regex.finditer(line)
	if li:
		if sti_flag:
			for i in li:
				item = i.group()
				single_term_idx[(item, docno)] += 1
				sti_fn = counterWriteToFile('single_term_idx', sti_fn, single_term_idx)
		line = regex.sub(',', line) # use comma as a position holder
	return line

def fileExtension(line, regex, docno, sti_flag):
	global sti_fn
	file_names = regex.finditer(line)
	if file_names:
		if sti_flag:
			for i in file_names:
				# store whole file
				single_term_idx[(i.group(), docno)] += 1
				sti_fn = counterWriteToFile('single_term_idx', sti_fn, single_term_idx)
				# store file extension
				single_term_idx[(i.group(2), docno)] += 1
				sti_fn = counterWriteToFile('single_term_idx', sti_fn, single_term_idx)
		line = regex.sub(',', line) # use comma as a position holder
	return line

def dotAcronym(match):
	temp = match.group()
	temp = temp.replace('.', '')
	return temp

def digitAlpha(line, regex, docno, sti_flag):
	global sti_fn
	pairs = regex.finditer(line)
	if pairs:
		if sti_flag:
			for pair in pairs:
				num, word = pair.group(1), pair.group(2)
				if len(word) >= 3 and not word in stop_words:
					single_term_idx[(word, docno)] += 1
					sti_fn = counterWriteToFile('single_term_idx', sti_fn, single_term_idx)
				single_term_idx[(num + word, docno)] += 1
				sti_fn = counterWriteToFile('single_term_idx', sti_fn, single_term_idx)
		line = regex.sub(',', line) # use comma as a position holder
	return line

def alphaDigit(line, regex, docno, sti_flag):
	global sti_fn
	pairs = regex.finditer(line)
	if pairs:
		if sti_flag:
			for pair in pairs:
				word, num = pair.group(1), pair.group(2)
				if len(word) >= 3 and not word in stop_words:
					single_term_idx[(word, docno)] += 1
					sti_fn = counterWriteToFile('single_term_idx', sti_fn, single_term_idx)
				single_term_idx[(word + num, docno)] += 1
				sti_fn = counterWriteToFile('single_term_idx', sti_fn, single_term_idx)
		line = regex.sub(',', line) # use comma as a position holder
	return line

def prefixReplace(line, regex, docno, sti_flag):
	global sti_fn
	words = regex.finditer(line)
	if words:
		if sti_flag:
			for word in words:
				stem = word.group(2)
				if not stem in stop_words:
					single_term_idx[(stem, docno)] += 1
					sti_fn = counterWriteToFile('single_term_idx', sti_fn, single_term_idx)
		line = regex.sub(r'\g<1>\g<2>', line)
	return line

def removeHyphen(match):
	return match.group().replace('-', '')

def hyphenReplace(line, regex, docno, sti_flag):
	global sti_fn
	words = regex.finditer(line)
	if words:
		if sti_flag:
			for i in words:
				word = i.group()
				li = word.split('-')
				for item in li:
					if not item in stop_words:
						single_term_idx[(item, docno)] += 1
						sti_fn = counterWriteToFile('single_term_idx', sti_fn, single_term_idx)
		line = regex.sub(removeHyphen, line)
	return line

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

def dateReplace(line, regex, docno, sti_flag):
	global sti_fn
	dates = regex.finditer(line)
	if dates:
		for i in dates:
			date = i.group()
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
				line.replace(date, '') # remove this date
				continue # go to next date
			if sti_flag:
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
				single_term_idx[(s_month+'/'+s_day+'/'+str(year), docno)] += 1
				sti_fn = counterWriteToFile('single_term_idx', sti_fn, single_term_idx)
		# end of for loop
		line = regex.sub(',', line)
	return line

def createIndexTables(args):
	global sti_fn, stpi_fn, si_fn, pi_fn
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
	p_email = re.compile(r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b', re.I)
	p_url = re.compile(r'\b(https?|ftp)://w{3}[a-z0-9_/.-]{2,}', re.I)
	p_file_extension = re.compile(r'([^\\\/:*?\"<>|\s]+)\.(aif|cda|mid|midi|mp3|mpa|ogg|wav|wma|wpl|7z|arj|deb|pkg|rar|rpm|tar\.gz|z|zip|bin|dmg|iso|toast|vcd|csv|dat|db|dbf|log|mdb|sav|sql|tar|xml|apk|bat|bin|cgi|pl|com|exe|gadget|jar|py|wsf|fnt|fon|otf|ttf|ai|bmp|gif|ico|jpeg|jpg|png|ps|psd|svg|tif|tiff|asp|aspx|cer|cfm|css|htm|html|js|jsp|part|php|rss|xhtml|key|odp|pps|ppt|pptx|class|cpp|cs|h|java|sh|swift|vb|ods|xlr|xls|xlsx|bak|cab|cfg|cpl|cur|dll|dmp|drv|icns|ico|ini|lnk|msi|sys|tmp|3g2|3gp|avi|flv|h264|m4v|mkv|mov|mp4|mpg|mpeg|rm|swf|vob|wmv|doc|docx|odt|pdf|rtf|tex|txt|wks|wps|wpd)', re.I)
	p_prefix = re.compile(r'\b(a|an|ante|anti|auto|circum|co|com|con|contra|contro|de|dis|en|em|ex|extra|fore|hetero|homo|homeo|hyper|il|im|in|ir|inter|intra|intro|macro|micro|mid|mis|mono|non|omni|over|post|pre|pro|re|semi|sub|super|sym|syn|trans|tri|un|under|uni)-([a-z])+\b', re.I)
	p_hyphen = re.compile(r'\b(\w+-)+\w+\b')
	p_ip = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\b')

	# build stop word set
	f = open('stops.txt', 'r')
	for line in f:
		stop_words.add(line.strip())
	f.close()
	# use a flag to decide whether to store special token in single term index table
	sti_flag = False
	if args.index_type == 'single':
		sti_flag = True
	stemmer = PorterStemmer() # create a porter stemmer
	files = glob.glob(args.input_dir+'*') # grab every file under input directory
	# create a tmp directory or remove everything under tmp directory for storing temporary files
	if not os.path.exists('tmp'):
		os.makedirs('tmp')
	else:
		rm_dir = glob.glob('./tmp/*')
		for f in rm_dir:
			os.remove(f)
	# start processing files
	for file in files:
		f = open(file, 'r')
		flag = False
		docno = 'NoDocNum' # indicate error
		pos = 0
		last_two_words = ['a', 'a'] # use two stop words
		for line in f:
			temp = line.strip()
			if temp.startswith('<DOCNO>'):
				docno = p_docno.match(temp).group(1).strip()
			elif temp == '<TEXT>':
				flag = True
				pos = 0
			elif temp == '</TEXT>':
				flag = False
			elif flag:
				# convert all character references (e.g. &gt;, &#62;, &x3e;) to unicode
				temp = replace_entities(temp)
				temp = html.unescape(temp)
				# remove <> tag and <!-- --> comments
				temp = p_tag_comment.sub('', temp)
				# convert to lower case
				temp = temp.lower()
				# grep email
				temp = specialToken(temp, p_email, docno, sti_flag)
				# grep url
				temp = specialToken(temp, p_url, docno, sti_flag)
				# grep file extension
				temp = fileExtension(temp, p_file_extension, docno, sti_flag)
				# grep ph.D etc.
				temp = p_dot_acronym.sub(dotAcronym, temp)
				# grep date
				temp = dateReplace(temp, p_date, docno, sti_flag)
				# digit format
				temp = p_num1.sub(r'\g<1>', temp) # remove ',' in 1,000
				temp = p_num2.sub(r'\g<1>', temp) # remove '.00' in 1.00
				# digit-alpha format
				temp = digitAlpha(temp, p_digit_alpha, docno, sti_flag)
				# alpha-digit format
				temp = alphaDigit(temp, p_alpha_digit, docno, sti_flag)
				# grep prefix
				temp = prefixReplace(temp, p_prefix, docno, sti_flag)
				# grep hyphenated word
				temp = hyphenReplace(temp, p_hyphen, docno, sti_flag)
				# grep ip
				temp = specialToken(temp, p_ip, docno, sti_flag)
				li = nltk.word_tokenize(temp)
				for (i, word) in enumerate(li):
					s = (word, docno)
					if not word in stop_words:
						if args.index_type == 'single':
							# build single term idx
							single_term_idx[s] += 1
							sti_fn = counterWriteToFile('single_term_idx', sti_fn, single_term_idx)
						elif args.index_type == 'stem':
							# build stem idx
							stem_idx[(stemmer.stem(word), docno)] += 1
							si_fn = counterWriteToFile('stem_idx', si_fn, stem_idx)
						elif args.index_type == 'phrase':
							# build phrase idx
							if i < 2:
								if i == 0 and not last_two_words[1] in stop_words:
									phrase_idx[(last_two_words[1]+' '+word, docno)] += 1
									pi_fn = counterWriteToFile('phrase_idx', pi_fn, phrase_idx)
									if not last_two_words[0] in stop_words:
										phrase_idx[(last_two_words[0]+' '+last_two_words[1]+' '+word, docno)] += 1
										pi_fn = counterWriteToFile('phrase_idx', pi_fn, phrase_idx)
								elif i == 1 and not li[0] in stop_words:
									phrase_idx[(li[0]+' '+word, docno)] += 1
									pi_fn = counterWriteToFile('phrase_idx', pi_fn, phrase_idx)
									if not last_two_words[1] in stop_words:
										phrase_idx[(last_two_words[1]+' '+li[0]+' '+word, docno)] += 1
										pi_fn = counterWriteToFile('phrase_idx', pi_fn, phrase_idx)
							elif not li[i - 1] in stop_words:
								phrase_idx[(li[i - 1]+' '+word, docno)] += 1
								pi_fn = counterWriteToFile('phrase_idx', pi_fn, phrase_idx)
								if not li[i - 2] in stop_words:
									phrase_idx[(li[i - 2]+' '+li[i - 1]+' '+word, docno)] += 1
									pi_fn = counterWriteToFile('phrase_idx', pi_fn, phrase_idx)
					if args.index_type == 'positional':
						# build single term position idx
						if not s in single_term_pos_idx:
							single_term_pos_idx[s] = [0]
						single_term_pos_idx[s][0] += 1
						single_term_pos_idx[s].append(pos)
						stpi_fn = orderedDictWriteToFile('single_term_pos_idx', stpi_fn, single_term_pos_idx)
						pos += 1
				# end of 'for' loop tokenizing one line
				if args.index_type == 'phrase':
					if len(li) >= 2:
						last_two_words[0] = li[-2]
						last_two_words[0] = li[-1]
					elif len(li) == 1:
						# move everything to the left and add a new word
						last_two_words[0] = last_two_words[1]
						last_two_words[1] = li[-1]
			# end of 'if' reading one line
		# end of reading one file
		f.close() # close the reading file
	# end of reading all files
	# write the remaining index tables to files
	if single_term_idx and args.index_type == 'single':
		# write single_term_idx to file
		f = open('tmp/single_term_idx_'+str(sti_fn)+'.txt', 'w', encoding='utf8')
		for key in sorted(single_term_idx.keys()):
			f.write(' '.join(str(x) for x in key)+' '+str(single_term_idx[key])+'\n')
		f.close()
		sti_fn += 1
		single_term_idx.clear()
		print('Number of single temp files:', sti_fn)
	elif single_term_pos_idx and args.index_type == 'positional':
		# write single_term_pos_idx to file
		f = open('tmp/single_term_pos_idx_'+str(stpi_fn)+'.txt', 'w', encoding='utf8')
		for key in single_term_pos_idx.keys():
			f.write(' '.join(str(x) for x in key)+' '+' '.join(str(x) for x in single_term_pos_idx[key])+'\n')
		f.close()
		stpi_fn += 1
		single_term_pos_idx.clear()
		print('Number of positional temp files:', stpi_fn)
	elif stem_idx and args.index_type == 'stem':
		# write stem_idx to file
		f = open('tmp/stem_idx_'+str(si_fn)+'.txt', 'w', encoding='utf8')
		for key in sorted(stem_idx.keys()):
			f.write(' '.join(str(x) for x in key)+' '+str(stem_idx[key])+'\n')
		f.close()
		si_fn += 1
		stem_idx.clear()
		print('Number of stem temp files:', si_fn)
	elif phrase_idx:
		# write phrase_idx to file
		f = open('tmp/phrase_idx_'+str(pi_fn)+'.txt', 'w', encoding='utf8')
		for key in sorted(phrase_idx.keys()):
			f.write(' '.join(str(x) for x in key)+' '+str(phrase_idx[key])+'\n')
		f.close()
		pi_fn += 1
		phrase_idx.clear()
		print('Number of phrase temp files:', pi_fn)

def parseSTI(line, idx):
	parts = line.split()
	# term, docno, term frequency
	return [(parts[0], parts[1]), int(parts[2]), idx]

def parseSTPI(line, idx):
	parts = line.split()
	# term, docno, term frequency, term positions
	return [(parts[0], parts[1]), int(parts[2]), parts[3:], idx]

def parseSI(line, idx):
	return parseSTI(line, idx)

def parsePI(line, idx):
	parts = line.split()
	if parts[2].startswith('FR'):
		return [(parts[0]+' '+parts[1], parts[2]), int(parts[3]), idx]
	else:
		return [(parts[0]+' '+parts[1]+' '+parts[2], parts[3]), int(parts[4]), idx]

def merge(li, parse, file_name, pos_idx_flag):
	# if there is no need to merge the file, make a copy
	if len(li) == 1:
		files = glob.glob('./tmp/*')
		li[0].close()
		shutil.copy(files[0], file_name)
		return
	lexicon = Counter() # used for calculating min_df, max_df, mean_df, median_df
	h = []
	# initialize heap
	for (i, f) in enumerate(li):
		line = f.readline().strip()
		if line:
			heapq.heappush(h, parse(line, i))
	# read one from heap to check repetition
	out = open(file_name, 'w')
	last_pop = heapq.heappop(h)
	line = li[last_pop[-1]].readline().strip()
	if line:
		heapq.heappush(h, parse(line, last_pop[-1]))
	pop = []
	# start n-way merging using heap
	while (h):
		pop = heapq.heappop(h)
		line = li[pop[-1]].readline().strip()
		if line:
			heapq.heappush(h, parse(line, pop[-1]))
		else:
			li[pop[-1]].close()
		if pop[0] == last_pop[0]:
			# combine repetition
			last_pop[1] += pop[1]
			if pos_idx_flag:
				last_pop[2] = sorted(last_pop[2] + pop[2])
		else:
			# no repetition, then write to file
			out.write(' '.join(last_pop[0])+' '+str(last_pop[1]))
			lexicon[last_pop[0][0]] += last_pop[1] # used for analysis
			if not pos_idx_flag:
				out.write('\n')
			else:
				out.write(' '+' '.join(last_pop[2])+'\n')
			last_pop = pop
	# write last line into file
	out.write(' '.join(last_pop[0])+' '+str(last_pop[1]))
	lexicon[last_pop[0][0]] += last_pop[1] # used for analysis
	if not pos_idx_flag:
		out.write('\n')
	else:
		out.write(' '+' '.join(last_pop[2])+'\n')
	out.close()
	# analysis
	print()
	print('Lexicon size:', len(lexicon))
	print('min:', min(lexicon.values()), 'max:', max(lexicon.values()), 'mean:', round(statistics.mean(lexicon.values()), 2), 'median:', statistics.median(lexicon.values()))
	print()

def createFrequentPhraseIndex(args, freq_limit):
	input_f = open(args.output_dir+'phrase_idx.txt', 'r')
	output_f = open(args.output_dir+'freq_phrase_idx.txt', 'w')
	c = Counter()
	for line in input_f:
		temp = parsePI(line, 0)
		c[temp[0][0]] += temp[1]
	input_f.close()
	input_f = open(args.output_dir+'phrase_idx.txt', 'r')
	for line in input_f:
		temp = parsePI(line, 0)
		if c[temp[0][0]] >= freq_limit:
			output_f.write(line)
	input_f.close()
	output_f.close()
	output_f = open(args.output_dir+'freq_phrase.txt', 'w')
	for item in c.keys():
		if c[item] >= freq_limit:
			output_f.write(item+'\n')
	output_f.close()

def mergeIndexTables(args):
	# create output directory if not exists
	if not os.path.exists(args.output_dir):
		os.makedirs(args.output_dir)
	# open files under tmp directory
	li = []
	files = glob.glob('./tmp/*')
	for file in files:
		li.append(open(file, 'r'))
	# do the n-way merge
	if args.index_type == 'single':
		merge(li, parseSTI, args.output_dir+'single_term_idx.txt', False)
	elif args.index_type == 'stem':
		merge(li, parseSI, args.output_dir+'stem_idx.txt', False)
	elif args.index_type == 'phrase':
		merge(li, parsePI, args.output_dir+'phrase_idx.txt', False)
	else:
		merge(li, parseSTPI, args.output_dir+'single_term_pos_idx.txt', True)

def parseCommand():
	parser = argparse.ArgumentParser(description='Build one type of index table.')
	parser.add_argument('input_dir', help='The directory containing the raw documents for input (e.g. fr940104.0).')
	parser.add_argument('index_type', choices=['single', 'stem', 'phrase', 'positional'], help='''Type of index table to build.
		("single": single term index table,
		"stem": stem index table,
		"phrase": phrase index table,
		"positional": single term position index table)''')
	parser.add_argument('output_dir', help='The directory containing the built index table.')
	args = parser.parse_args()
	if 'tmp' in args.input_dir:
		print('error: tmp is not allowed as input directory.', file=sys.stderr)
		exit(1)
	if 'tmp' in args.output_dir:
		print('error: tmp is not allowed as output directory.', file=sys.stderr)
		exit(1)
	if args.input_dir[0] == '/':
		args.input_dir = '.' + args.input_dir
	if args.output_dir[0] == '/':
		args.output_dir = '.' + args.output_dir
	if args.input_dir[-1] != '/':
		args.input_dir += '/'
	if args.output_dir[-1] != '/':
		args.output_dir += '/'
	return args

if __name__ == '__main__':
	args = parseCommand()
	t1 = time.time()
	createIndexTables(args)
	stop_words.clear() # no longer useful, cleared to save memory
	t2 = time.time()
	mergeIndexTables(args)
	if args.index_type == 'phrase':
		createFrequentPhraseIndex(args, 70)
	t3 = time.time()
	print('Time to create temp files:', round(1000*(t2 - t1), 2), 'ms')
	print('Time to merge temp files:', round(1000*(t3 - t2), 2), 'ms')
	print('Total time:', round(1000*(t3 - t1), 2), 'ms')