from django.contrib import admin

from .models import Category, Product, Menu, MenuItem, MenuTree

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Menu)
admin.site.register(MenuItem)
admin.site.register(MenuTree)
