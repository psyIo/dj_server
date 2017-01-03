from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

from .add_lib import logme, add_li
from .models import Category, Product, Menu, MenuItem, MenuTree

def index(request):
	resp = []
	root = MenuTree()
	root = root.get_root()
	tree = root.get_tree()
	elem_qty = len(tree)
	return render(request, 'menu_app/menu_active.html',{#'menu': menu, 
														'tree': tree,
														'elem_qty': elem_qty})

def insert_child(request, node, is_cat, rel_id):
	'''
	/insch/78/1/1/
	'''
	try:
		parent = MenuTree.objects.get(id=node)	
		parent.insert_child(is_cat,rel_id)
	except:
		return HttpResponse('Error: creating child')
	return HttpResponse('Ok: child created')

def insert_sibling(request, node, is_cat, rel_id):
	'''
	/inssib/78/1/1/
	'''
	try:
		parent = MenuTree.objects.get(id=node)
		parent.insert_sibling(is_cat,rel_id)
	except:
		return HttpResponse('Error: creating sibling')
	return HttpResponse('Ok: sibling created')

def category_card(request, cat_id):
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
	try:
		menu = MenuTree.objects.get(id=int(element_id))
	except ObjectDoesNotExist:	
		raise ObjectDoesNotExist('Element does not exist') #??
	menu.delete_element(True)
	return redirect('menu_admin')		

def generate_tree(request):
	root = MenuTree()
	root = root.get_root()
	root.generate_random_tree()
	return redirect('menu_admin')

def menu_admin(request):
	root = MenuTree()
	root = root.get_root()
	tree = root.get_tree()
	elem_qty = len(tree)
	cats = Category.objects.all()
	prods = Product.objects.all()	
	return render(request, 'menu_app/menu.html',{'tree': tree, 
												 'elem_qty': elem_qty,
												 'cats': cats,
												 'prods': prods})

def delete_tree(request):
	all_obj = MenuTree.objects.all()
	all_obj.delete()
	return redirect('menu_admin')