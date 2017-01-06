from django.db import models
from django.db.models import F
from django.core import exceptions
from .add_lib import logme, add_li, attr_to_string, obj_w_level_to_list
import random
import datetime

class Category(models.Model):
	name = models.TextField(max_length=50)
	active = models.BooleanField(default=False)

	def save(self, *args, **kwargs):
		if self.name == 'root':
			try:
				root = Category.objects.filter(name='root')
			except:
				root = None
			if root:
				return False				
		super(Category, self).save(*args, **kwargs)

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

	def update_parents_element_count(self, changes): #, active):
		'''
		Updates child_qty and child_qty_active fields for all parents
		changes = [child_qty,child_qty_active]
		'''	
		self.child_qty = F('child_qty') + changes[0]
		self.child_qty_active = F('child_qty_active') + changes[1]
		self.save()
		self.refresh_from_db()			
		if self.parent:			
			self.parent.update_parents_element_count(changes)	
		return	

	def get_root(self):
		'''
		Returns root element, creates if does not exist, with category name 'root'
		'''
		try:
			root = MenuTree.objects.get(parent=None)
		except exceptions.ObjectDoesNotExist:
			root = MenuTree()
			root.is_category = True
			try:
				cat = Category.objects.filter(name='root')[0]
				if not cat.active:
					cat.active = True
					cat.save()
			except:
				cat = Category()
				cat.name = 'root'
				cat.active = True
				cat.save()
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
			if child.product.active and self.category.active and not self.parent_category_inactive():
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
			if sibling.product.active and sibling.parent.parent_category_inactive():
				sibling.parent.update_parents_element_count([1,1])
			else:
				sibling.parent.update_parents_element_count([1,0])

		return sibling	

	def parent_category_inactive(self):
		'''
		Checks if exist inactive parent category
		'''
		parent = self.parent
		while parent:
			if not parent.category.active:
				return True
			parent = parent.parent
		return False

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
					deleted_products = [x + y for x, y in 
										zip(deleted_products, child.delete_element(False))]			
			else:
				run_loop = False
		return deleted_products

	def delete_element(self, update_parents):
		'''
		Deletes element and childs if category
		returns a list of deleted child_qty and child_qty_active quantities
		'''
		deleted_products = [0,0]
		if self.top_sib:
			self.top_sib.bot_sib = self.bot_sib
			self.top_sib.save()
		if self.bot_sib:
			self.bot_sib.top_sib = self.top_sib
			self.bot_sib.save()
	
		if self.is_category:			
			deleted_products = self.delete_category_childs()
			if not self.category.active or self.parent_category_inactive():
				deleted_products[1] = 0 #active products
		else: #product	
			if self.product.active and not self.parent_category_inactive():
				deleted_products = [1,1]
			else:
				deleted_products = [1,0]

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

	def get_tree(self):	
		'''
		Retruns tree objects list
		'''
		tree = []
		root = self.get_root()
		obj_w_level_to_list(tree, root, 0)
		tree += root.get_category_branch()
		return tree		

	def get_category_branch(self, level=0, *args, **kwargs):
		'''
		Returns list of MenuTree objects, that are childs of self
		'''			
		local_level = level + 1
		branch = []
		if self.first_child:
			run_loop = True
			while run_loop:
				if self.first_child.is_category:
					obj_w_level_to_list(branch,self.first_child,local_level)
					branch += self.first_child.get_category_branch(local_level)
				else:
					obj_w_level_to_list(branch,self.first_child,local_level)
				if not self.first_child.bot_sib:  #last child element
					run_loop = False
				else:
					self.first_child = self.first_child.bot_sib
		return branch

	def get_single_branch(self):
		'''
		Returns single level child elements
		'''
		branch = []
		if self.first_child:
			run_loop = True
			while run_loop:
				obj_w_level_to_list(branch,self.first_child,self.get_level()+1)
				if not self.first_child.bot_sib:  #last child element
					run_loop = False
				else:
					self.first_child = self.first_child.bot_sib
		return branch

	def generate_random_tree(self):
		'''
		Generates total_elements random tree 
		'''
		total_cats = 300
		total_prods = 10000
		total_elements = 500

		start = datetime.datetime.now()
		logme('generate_random_tree process started {}'.format(start))
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

		root = self.get_root()
		elements_left = total_elements
		for i in range(total_elements):
			elements_left -= root.create_random_child(elements_left,1)
			if elements_left < 1:
				break
		end = datetime.datetime.now()
		logme('generate_random_tree process finished, duration {}, elements created {}'.format(end - start,total_elements))
			
	def create_random_child(self, elements_left, level):
		'''
		Creates random child, if child is category makes recursion call 
		to generate its childs until elements_left == created_childs
		'''
		stop_prob = 0.2
		prod_prob = 0.8 #else category
		prod_in_first_level_prob = 0.1		
		cats = Category.objects.all()
		prods = Product.objects.all()
		created_childs = 0
		for i in range(elements_left):
			if (random.random() <= stop_prob) or (created_childs > elements_left):
				break
			elif level == 1:
				insert_prod = random.random() <= prod_in_first_level_prob
			else:
				insert_prod = random.random() <= prod_prob
			if insert_prod:
				child = self.insert_child(False,random.choice(prods).id)
				created_childs += 1
			else: #category
				cat = self.insert_child(True,random.choice(cats).id)
				created_childs += 1
				created_childs += cat.create_random_child(elements_left - created_childs, level + 1)
		return created_childs

	def get_level(self):
		'''
		Returns level of self element
		'''
		level = 0
		parent = self.parent
		while parent:
			level += 1
			parent = parent.parent
		return level
