from django.db import models
from django.db.models import F
from django.core import exceptions
from .add_lib import logme, add_li, attr_to_string, obj_w_level_to_list
import random

class Category(models.Model):
	name = models.TextField(max_length=50)
	active = models.BooleanField(default=False)

class Product(models.Model):
	name = models.TextField(max_length=50)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	active = models.BooleanField(default=False)

class MenuTree(models.Model):
	parent = models.ForeignKey('self', related_name='parent_to_self',
							   blank=True, null=True, db_index=True)
	first_child = models.ForeignKey('self', related_name='first_child_to_self',
		                       blank=True, null=True, db_index=True)
	top_sib = models.ForeignKey('self', related_name='top_sib_to_self',
						       blank=True, null=True, db_index=True)
	bot_sib = models.ForeignKey('self', related_name='bot_sib_to_self',
							   blank=True, null=True, db_index=True)
	is_category = models.BooleanField()
	category = models.ForeignKey(Category, related_name='menu_tree_to_category', 
							   blank=True, null=True)
	product = models.ForeignKey(Product, related_name='menu_tree_product',
							   blank=True, null=True)
	child_qty = models.IntegerField(default=0)
	child_qty_active = models.IntegerField(default=0)


	# def save(self, *args, **kwargs):
	# 	if not self.parent: #root element
	# 		pass
	# 	super(MenuTree, self).save(*args, **kwargs)

	def update_parents_element_count(self, changes): #, active):
		'''
		Updates child_qty and child_qty_active fields for all parents
		changes = [child_qty,child_qty_active]
		'''	
		self.child_qty = F('child_qty') + changes[0]
		self.child_qty_active = F('child_qty_active') + changes[1]
		self.save()
		self.refresh_from_db() #dev				
		if self.parent:			
			self.parent.update_parents_element_count(changes)	
		pats = MenuTree.objects.get(id=self.id)
		pats.refresh_from_db()
		logme('Updated elements for pats id: {} change {} total elements {}'.format(
				pats.id,changes[0],pats.child_qty))
		return
	

	def get_root(self):
		'''
		Returns Root element, creates if does not exist, and assigns first active
		category if exist
		'''
		try:
			root = MenuTree.objects.get(parent=None)
		except exceptions.ObjectDoesNotExist:
			root = MenuTree()
			root.is_category = True
			try:
				cat = Category.objects.filter(active=True)[0]
			except:
				cat = None
			root.category = cat	
			root.save()
		return root

	def insert_child(self, child_is_category, link_id, *args, **kwargs):
		"""
		Always inserts first child, pushing ex_first_child down if exist
		link_id = id of Category or Product models
		"""
		if not self.is_category:
			raise exceptions.FieldError("Child can be inserted only in category")

		child = MenuTree()
		child.parent = self
		child.is_category = bool(int(child_is_category))
		if child.is_category:
			try:
				cat = Category.objects.get(id=int(link_id))
			except exceptions.ObjectDoesNotExist:	
				raise exceptions.FieldError('Existing Category must be set')	
			child.category = cat
		else:
			try:
				prod = Product.objects.get(id=int(link_id))
			except exceptions.ObjectDoesNotExist:	
				raise exceptions.FieldError('Existing Product must be set')	
			child.product = prod

		if self.first_child:
			child.bot_sib = self.first_child
			child.save()
			self.first_child.top_sib = child
			self.first_child.save()			
		else:
			child.bot_sib = None
			child.save()

		self.first_child = child
		if not child.is_category:
			logme('created child id {}'.format(child.id)) #dev
			if child.product.active:
				self.update_parents_element_count([1,1])
			else:
				self.update_parents_element_count([1,0])
		else:
			self.save()
		return child

	def insert_sibling(self, sibling_is_category, link_id, *args, **kwargs):
		"""
		Always inserts sibling after self
		"""	
		if not self.parent:
			raise exceptions.FieldError('Root element can not have siblings')

		sibling = MenuTree()
		sibling.parent = self.parent
		sibling.first_child = None
		sibling.top_sib = self
		sibling.is_category = bool(int(sibling_is_category))
		if sibling.is_category:
			try:
				cat = Category.objects.get(id=int(link_id))
			except exceptions.ObjectDoesNotExist:	
				raise exceptions.FieldError('Category must be set')	
			sibling.category = cat
		else:
			try:
				prod = Product.objects.get(id=int(link_id))
			except exceptions.ObjectDoesNotExist:	
				raise exceptions.FieldError('Product must be set')	
			sibling.product = prod

		sibling.bot_sib = self.bot_sib #None or object
		sibling.save()

		if self.bot_sib:
			self.bot_sib.top_sib = sibling
			self.bot_sib.save()

		self.bot_sib = sibling	
		self.save()

		#updates child qtys in parent entry		
		if not sibling.is_category:
			logme('created sibling element id {}'.format(sibling.id)) #dev
			if sibling.product.active:
				#parent.update_parents_element_count([1,1])
				sibling.parent.update_parents_element_count([1,1])
			else:
				sibling.parent.update_parents_element_count([1,0])

		return sibling	

	def delete_category_childs(self):
		'''
		Returns a list of deleted child_qty and child_qty_active
		'''
		deleted_products = [0,0]
		run_loop = True
		while run_loop:		
			if self.first_child:
				try:
					child = MenuTree.objects.get(id=self.first_child.id)
				except exceptions.ObjectDoesNotExist:
					child = None
					self.first_child = child
					run_loop = False

				if child:
					self.first_child = child.bot_sib
					#deleted_products += child.delete_element(False)	
					deleted_products = [x + y for x, y in 
										zip(deleted_products, child.delete_element(False))]			
			else:
				run_loop = False
		# logme('2 self: id {} first_ch {} del-prod {}'.format(
		# 		self.id, self.first_child, deleted_products))
		return deleted_products

	def delete_element(self, update_parents):
		'''
		Returns a list of deleted child_qty and child_qty_active
		'''
		#top_sib = bot_sib = None
		deleted_products = [0,0]
		# if self.top_sib:
		# 	try:
		# 		top_sib = MenuTree.objects.get(id=self.top_sib.id)
		# 	except exceptions.ObjectDoesNotExist:
		# 		pass

		# if self.bot_sib:
		# 	try:
		# 		bot_sib = MenuTree.objects.get(id=self.bot_sib.id)
		# 	except exceptions.ObjectDoesNotExist:
		# 		pass

		# if top_sib:
		# 	top_sib.bot_sib = bot_sib
		# 	top_sib.save()

		# if bot_sib:
		# 	bot_sib.top_sib = top_sib
		# 	bot_sib.save()	
		if self.top_sib:
			self.top_sib.bot_sib = self.bot_sib
			self.top_sib.save()
		if self.bot_sib:
			self.bot_sib.top_sib = self.top_sib
			self.bot_sib.save()
		#logme('top_sib {} bot_sib {}'.format(top_sib,bot_sib))	
	
		if self.is_category:
			deleted_products = self.delete_category_childs()
		else: #product	
			if self.product.active:
				deleted_products = [1,1]
			else:
				deleted_products = [1,0]

		# if self.parent:		
		# 	try:
		# 		parent = MenuTree.objects.get(id=self.parent.id)
		# 	except exceptions.ObjectDoesNotExist:
		# 		parent = None
		# else: #root element
		# 	parent = None

		# if parent:
		# 	if parent.first_child == self: #self is a first child
		# 		parent.first_child = self.bot_sib
		# 		parent.save()
		# 	if update_parents and (deleted_products[0] != 0):	
		# 		parent.update_parents_element_count([-1 * x for x in deleted_products])
		if self.parent:
			if self.parent.first_child == self: #self is a first child
				self.parent.first_child = self.bot_sib
				self.parent.save()
			if update_parents and (deleted_products[0] != 0):
				self.parent.update_parents_element_count([-1 * x for x in deleted_products])

		self.parent = None 
		self.top_sib = None
		self.bot_sib = None
		self.delete()				
		return deleted_products

	def get_tree_ul(self, level=0, *args, **kwargs):		
		resp = []
		local_level = level + 1
		try:
			submenu = MenuTree.objects.filter(parent=self, top_sib=None).get()
		except exceptions.ObjectDoesNotExist:	
			submenu = None		
		if submenu: # != None:	
			logme(submenu,'submenu_ne_none')
			logme(submenu.is_category,'submenu.is_category')		
			if submenu.is_category:
				if submenu.category:
					if submenu.category.active:
						add_li(resp,'--'*local_level+str(submenu.id)+' '
							   +str(submenu.category.name)+' '+str(submenu.child_qty)
							   +' <a href="/del/{}">del</a>'.format(submenu.id))
						resp.append(submenu.get_tree_ul(local_level))
			else:
				logme(submenu,'submenu_ne_noneX')
				if submenu.product:
					if submenu.product.active:
						add_li(resp,'--'*local_level+str(submenu.id)+' '+str(submenu.product.name)
							   +' '+str(submenu.product.price)+' <a href="/del/{}">del</a>'.format(submenu.id))
			run_loop = True
			while run_loop:				
				if submenu.bot_sib == None:  #last child element
					run_loop = False
				else:
					try:
						bot_sib = MenuTree.objects.get(id=submenu.bot_sib.id)
					except exceptions.ObjectDoesNotExist:
						run_loop = False
						bot_sib = None				

					if bot_sib != None:						
						if bot_sib.is_category:
							if bot_sib.category:
								if bot_sib.category.active:
									add_li(resp,'--'*local_level+str(bot_sib.id)+' '
										   +str(bot_sib.category.name)+' '+str(bot_sib.child_qty)
										   +' <a href="/del/{}">del</a>'.format(bot_sib.id))
									resp.append(bot_sib.get_tree_ul(local_level))
						else:
							if bot_sib.product:
								if bot_sib.product.active:
									add_li(resp,'--'*local_level+str(bot_sib.id)+' '
										   +str(bot_sib.product.name)+' '+str(bot_sib.product.price)
										   +' <a href="/del/{}">del</a>'.format(bot_sib.id))
						submenu = MenuTree.objects.get(id=bot_sib.id)	

		return ''.join(resp)

	def get_tree(self):		
		tree = []
		root = self.get_root() #always category
		obj_w_level_to_list(tree, root, 0)
		tree += root.get_category_branch()
		return tree

	def get_category_branch(self, level=0, *args, **kwargs):
		'''
		Returns list of MenuTree objects, that are childs of self
		'''			
		local_level = level + 1
		branch = []
		# try:
		# 	if self.first_child:			
		# 		child = MenuTree.objects.get(id=self.first_child.id)
		# 	else:
		# 		child = None
		# except exceptions.ObjectDoesNotExist:	
		# 	child = None	
		# if child:
		if self.first_child:
			run_loop = True
			while run_loop:
				if self.first_child.is_category:
					#if child.category:
					#	if child.category.active:
					obj_w_level_to_list(branch,self.first_child,local_level)
					branch += self.first_child.get_category_branch(local_level)
				else:
					obj_w_level_to_list(branch,self.first_child,local_level)
				if not self.first_child.bot_sib:  #last child element
					run_loop = False
				else:
					#if self.first_child.bot_sib:
					self.first_child = self.first_child.bot_sib
					# try:
					# 	child = MenuTree.objects.get(id=child.bot_sib.id)
					# except exceptions.ObjectDoesNotExist:
					# 	run_loop = False
		return branch

	def generate_random_tree(self):
		total_cats = 300
		total_prods = 10000
		total_elements = 500
		#choices = [0,1,2,3]

		#cat = Category.objects.all()
		logme('generate_random_tree process started') #dev
		existing_cats = Category.objects.count()
		if existing_cats < total_cats:
			for i in range(total_cats - existing_cats):
				new_cat = Category()
				new_cat.name = 'Category_auto_{}'.format(i)
				new_cat.active = random.choice([True,True,True,False])
				new_cat.save()

		existing_prods = Product.objects.count()
		if existing_prods < total_prods:
			for i in range(total_prods - existing_prods):
				new_prod = Product()
				new_prod.name = 'Product_auto_{}'.format(i)
				new_prod.active = random.choice([True,True,True,False])
				new_prod.price = random.randrange(1000) + random.randrange(100)/100
				new_prod.save()

		# cats = Category.objects.all()
		# prods = Product.objects.all()
		root = self.get_root()
		#child = self.insert_child(True,random.choice(cats).id)
		#child = self.insert_child(False,random.choice(prods).id)
		debug_int = 0 #dev
		elements_left = total_elements
		for i in range(total_elements):
			elements_left -= root.create_random_child(elements_left)
			if elements_left < 1:
				break
			
	def create_random_child(self, elements_left):
		stop_prob = 0.3
		prod_prob = 0.7 #else category
		cats = Category.objects.all()
		prods = Product.objects.all()
		#go_deeper_prob = 0.5
		#active_prob = 0.9 #else not active
		created_childs = 0
		for i in range(elements_left):
			if (random.random() <= stop_prob) or (created_childs > elements_left):
				break
			elif random.random() <= prod_prob:
				child = self.insert_child(False,random.choice(prods).id)
				created_childs += 1
			else: #category
				cat = self.insert_child(True,random.choice(cats).id)
				created_childs += 1
				created_childs += cat.create_random_child(elements_left - created_childs)
		return created_childs



class Menu(models.Model):
	category = models.ForeignKey(Category, related_name='menu_to_category')

class MenuItem(models.Model):
	'''
	Menu Items model	
	'''
	menu = models.ForeignKey(Menu, related_name='menu_item_to_menu')
	is_category = models.BooleanField()
	category = models.ForeignKey(Category, related_name='menu_item_to_category', blank=True, null=True)
	product = models.ForeignKey(Product, related_name='menu_item_product', blank=True, null=True)

	def save(self, *args, **kwargs):
		#logme(self.is_category)
		#logme(self.category)
		#logme(self.product)
		# if self.is_category:
		# 	if self.category == None:
		# 		raise exceptions.FieldError('Category must be set')
		# else:	
		# 	if self.product == None:
		# 		raise exceptions.FieldError('Product must be set')
		super(MenuItem, self).save(*args, **kwargs)