from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist, FieldError

from .add_lib import logme, add_li, get_tabulating_string
from .models import Category, Product, MenuTree

def index(request):
	'''
	Non editable menu view
	'''
	resp = []
	root = MenuTree()
	root = root.get_root()
	# tree = root.get_tree()
	tree = root.get_single_branch()	
	elem_qty = len(tree) + 1
	li_tag = '<li class="tree_li"'
	return render(request, 'menu_app/menu_active.html',{'tree': tree,
														'elem_qty': elem_qty,
														'root': root,
														'li_tag': li_tag})

def insert_child(request, node, is_cat, rel_id):
	'''
	Inserts child for parent node
	is_cat (is_category) = 0 or 1
	url like: /insch/78/1/1/
	'''
	try:
		parent = MenuTree.objects.get(id=node)	
		parent.insert_child(is_cat,rel_id)
	except Exception as e:
		return HttpResponse('Error: ' + str(e))
	return HttpResponse('Ok: child created')

def insert_sibling(request, node, is_cat, rel_id):
	'''
	Inserts sibling for node element
	is_cat (is_category) = 0 or 1
	url like: /inssib/78/0/10/
	'''
	try:
		top_sibling = MenuTree.objects.get(id=node)
		top_sibling.insert_sibling(is_cat,rel_id)
	except FieldError as e:
		return HttpResponse('Error: ' + str(e))
	return HttpResponse('Ok: sibling created')

def category_card(request, cat_id):
	'''
	Shows category card view
	'''
	try:
		cat = Category.objects.get(id=int(cat_id))
	except ObjectDoesNotExist:	
		return HttpResponse('<h1>Category Does Not Exist</h1>')	
	resp = []
	resp.append('<h1>')
	resp.append(cat.name)
	resp.append('</h1>')
	resp.append('<p>Active ')
	resp.append(str(cat.active))
	resp.append('</p>')
	return HttpResponse(''.join(resp))

def product_card(request, prod_id):
	'''
	Shows product card view
	'''
	try:
		prod = Product.objects.get(id=int(prod_id))
	except ObjectDoesNotExist:	
		return HttpResponse('<h1>Category Does Not Exist</h1>')	
	resp = []
	resp.append('<h1>')
	resp.append(prod.name)
	resp.append('</h1>')
	resp.append('<p>Active: ')
	resp.append(str(prod.active))
	resp.append(' Price: ')
	resp.append(str(prod.price))
	resp.append('</p>')
	return HttpResponse(''.join(resp))

def delete_element(request, element_id):
	'''
	Deletes tree element
	'''	
	try:
		menu = MenuTree.objects.get(id=int(element_id))
	except ObjectDoesNotExist:	
		return redirect('menu_admin')
	menu.delete_element(True)
	return redirect('menu_admin')		

def generate_tree(request):
	'''
	Generates random tree
	'''
	root = MenuTree()
	root = root.get_root()
	root.generate_random_tree()
	return redirect('menu_admin')

def menu_admin(request):
	'''
	Editable version menu view
	'''
	root = MenuTree()
	root = root.get_root()
	tree = root.get_tree()
	cats_inactive = 0
	prods_inactive = 0
	active_prods_in_inactive_cats = 0
	prods_total = 0
	for item in tree:
		if item.is_category:
			if not item.category.active:
				cats_inactive += 1
		else:
			prods_total += 1
			if not item.product.active:
				prods_inactive += 1
			elif item.parent_category_inactive():
				active_prods_in_inactive_cats += 1

	elements_total = len(tree)
	cats_total = elements_total - prods_total
	cats = Category.objects.all()
	prods = Product.objects.all()
	return render(request, 
		'menu_app/menu.html',{'tree': tree, 
							  'elements_total': elements_total,
							  'cats': cats,
							  'prods': prods,
							  'cats_inactive': cats_inactive,
							  'prods_inactive': prods_inactive,
							  'prods_total': prods_total,
							  'cats_total': cats_total,
							  'active_prods_in_inactive_cats': active_prods_in_inactive_cats})

def delete_tree(request):
	'''
	Deletes whole tree
	'''
	all_obj = MenuTree.objects.all()
	all_obj.delete()
	return redirect('menu_admin')

def wrap_in_li(li_list,tree_obj):
	'''
	Wraps MenuTree obj in li and adds to list
	'''
	wrap_element = False
	if tree_obj.is_category:			
		if tree_obj.category.active:
			wrap_element = True	
	else:
		if tree_obj.product.active:
			wrap_element = True
	if wrap_element:		
		li_list.append('<li class="tree_li" id="li_{}">'.format(tree_obj.id))
		li_list.append(get_tabulating_string(tree_obj.get_level()))	
		li_list.append(str(tree_obj.id))
		if tree_obj.is_category:
			li_list.append(' <a class="expand_btn" href="javascript:void(0)" \
				data-id="{}" data-state="closed" onclick="expand_pressed(this)\
				">+</a>'.format(tree_obj.id))		
			li_list.append(' <a class="category" \
				href="/cat/{}">{}</a>'.format(tree_obj.category.id,tree_obj.category.name))
			li_list.append(' ({})'.format(tree_obj.child_qty_active))
		else:
			li_list.append(' <a class="product" \
				href="/prod/{}">{}</a>'.format(tree_obj.product.id,tree_obj.product.name))
			li_list.append(' (€ {})'.format(tree_obj.product.price))
		li_list.append('</li>')	

def get_childs_li(request, parent_id):
	'''
	Returns category childs wraped in <li> elements
	'''
	li_list = []
	try:
		child = MenuTree.objects.get(parent=parent_id, top_sib=None)
	except:
		child = None
	while child:
		wrap_in_li(li_list,child)
		child = child.bot_sib	
	if len(li_list) == 0:
		return HttpResponse('Error: Category has no child elements')
	else:
		return HttpResponse(''.join(li_list))
		
