from django.utils import timezone

def logme(obj_to_log,type='0'):
	'''
	console log functiom
	'''
	print ('++++++++ ' + '{:%y.%m.%d %H:%M:%S}'.format(
		timezone.now()) + ' [{}] '.format(type) + repr(obj_to_log))

def add_li(list_to_add,li_txt):
	list_to_add.append('<li class="tree_li">')
	list_to_add.append(li_txt)
	list_to_add.append('</li>')

def attr_to_string(obj):
	ret = []
	for attr, value in obj.__dict__.items():
		ret.append('{}='.format(attr))
		ret.append('{} '.format(value))
	return ''.join(ret)

def obj_w_level_to_list(list_to_add, obj, level_to_add):
	'''
	Add obj to a given list and level
	'''
	obj.level = level_to_add
	obj.level_string = (get_tabulating_string(level_to_add))
	list_to_add.append(obj)

def get_tabulating_string(level):
	# child_level = child.get_level()
	if level > 1:						
		return '<span class="space">{}</span>- '.format('--' * (level-1))
	# li_list.append('- ')
	else:
		return '- '

