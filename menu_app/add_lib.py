from django.utils import timezone

def logme(obj_to_log,type='0'):
	print ('++++++++ ' + '{:%y.%m.%d %H:%M:%S}'.format(
		timezone.now()) + ' [{}] '.format(type) + repr(obj_to_log))

def add_li(list_to_add,li_txt):
	list_to_add.append('<li>')
	list_to_add.append(li_txt)
	list_to_add.append('</li>')

def attr_to_string(obj):
	ret = []
	for attr, value in obj.__dict__.items():
		ret.append('{}='.format(attr))
		ret.append('{} '.format(value))
		#ret.append('\n')
	return ''.join(ret)

def obj_w_level_to_list(list_to_add, obj, level_to_add):
	obj.level = level_to_add
	obj.level_string = '--' * level_to_add
	list_to_add.append(obj)

