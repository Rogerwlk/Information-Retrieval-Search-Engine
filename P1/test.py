import re

p_date = re.compile(r"""\b
	([0-9]{1,2}-[0-9]{1,2}-[0-9]{2,4})
	|(((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.]?
	|January|February|March|April|May|June|July|August
	|September|October|November|December)
	\ [0-9]{1,2}(st|nd|rd|th)?,\ [0-9]{2,4})
 	\b""", re.VERBOSE)
p_num1 = re.compile(r',([0-9]{3})')
p_num2 = re.compile(r'\d+[.]\d+')

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
	match = match.group()
	month = day = year = 0
	if match[0] >= '0' and match[0] <= '9':
		date = match.split('-')
		month, day, year = int(date[0]), int(date[1]), int(date[2])
	else:
		date = match.split()
		t_m, t_d, year = date[0], date[1], int(date[2])
		if t_m[0] == 'J':
			if t_m[1] == 'a':
				month = 1
			elif t_m[2] == 'n':
				month = 6
			else:
				month = 7
		elif t_m[0] == 'F':
			month = 2
		elif t_m[0] == 'M':
			if t_m[2] == 'r':
				month = 3
			else:
				month = 5
		elif t_m[0] == 'A':
			if t_m[1] == 'p':
				month = 4
			else:
				month = 8
		elif t_m[0] == 'S':
			month = 9
		elif t_m[0] == 'O':
			month = 10
		elif t_m[0] == 'N':
			month = 11
		else:
			month = 12

		if t_d[1] >= '0' and t_d[1] <= '9':
			day = 10 * int(t_d[0]) + int(t_d[1])
		else:
			day = int(t_d[0])

	if not validDate(month, day, year):
		return ''
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

# p_date = re.compile(r"""\b
# 	([0-9]{1,2}-[0-9]{1,2}-[0-9]{2,4})
# 	|(((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.]?
# 	|January|February|March|April|May|June|July|August
# 	|September|October|November|December)
# 	\ [0-9]{1,2}(st|nd|rd|th)?,\ [0-9]{2,4})
#  	\b""", re.X)

# p_value = re.compile(r',([0-9]{3})')

def round_number(match):
	print(docno)
	return str(round(float(match.group())))

p_num1 = re.compile(r',([0-9]{3})')
p_num2 = re.compile(r'\b(\d+)[.]0+\b')
temp = '1,000,000.001'
temp = p_num1.sub(r'\g<1>', temp) # remove ',' in 1,000
temp = p_num2.sub(r'\g<1>', temp) # remove '.00' in 1.00
print(temp)
# print(p_date.sub(dateReplace, '05-07-18   Jan 31, 2012   March 3rd, '))
# temp = p_num1.sub(r'\g<1>', 'abc 1,000,000')
# docno = 1
# print(p_num2.sub(round_number, temp))

# p_docno = re.compile(r'(?:<DOCNO>\s*)(.+)(?:\s*</DOCNO>)')
# print(p_docno.search('<DOCNO> FR940104-0-00021 </DOCNO>').group(1))