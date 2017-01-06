from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index,name='index'),  
    url(r'^insch/(?P<node>\d+)/(?P<is_cat>\d{1})/(?P<rel_id>\d+)/$', 
    	views.insert_child, name='insert_child'), 
	url(r'^inssib/(?P<node>\d+)/(?P<is_cat>\d{1})/(?P<rel_id>\d+)/$', 
    	views.insert_sibling, name='insert_sibling'), 
	url(r'^cat/(?P<cat_id>\d+)/$', 
    	views.category_card, name='category_card'), 
	url(r'^prod/(?P<prod_id>\d+)/$', 
    	views.product_card, name='product_card'), 
	url(r'^del/(?P<element_id>\d+)/$', 
    	views.delete_element, name='delete_element'),
	url(r'^generate_tree/$', 
    	views.generate_tree, name='generate_tree'),
    url(r'^delete_tree/$', 
        views.delete_tree, name='delete_tree'),
    url(r'^menu_admin/$', 
        views.menu_admin, name='menu_admin'),
    url(r'^get_childs_li/(?P<parent_id>\d+)/$', 
        views.get_childs_li, name='get_childs_li'),
]