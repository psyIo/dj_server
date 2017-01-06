//js scripts for menu_app

function getCategory(){
    $input = $("input#category_input");
    val = $input.val();
    list = $input.attr('list'),
    match = $('#' + list + ' option').filter(function() {
       return ($(this).val() === val);
    });
    if(match.length > 0) {
        return match.data('id');
    };
    return;    
};

function getProduct(){
    $input = $("input#product_input");
    val = $input.val();
    list = $input.attr('list'),
    match = $('#' + list + ' option').filter(function() {
       return ($(this).val() === val);
    });
    if(match.length > 0) {
        return match.data('id');
    };
    return;    
};

function getChildCheckbox(){
    chbox = $('input#child_checkbox');
    return chbox.prop('checked');    
};

function getCategoryRadio(){
    cat_radio = $('input#category_radio');
    return cat_radio.prop('checked'); 
};

function createMenuEntry(){
    $('div#change_menu').toggleClass('invisible','visible');
    category_id = getCategory();
    product_id = getProduct();
    create_child = getChildCheckbox();
    create_category = getCategoryRadio();
};

function expand_pressed(self){
    //Expend category button pressed    
    var btn = $(self);
    var parent = btn.parent();
    var request = '/get_childs_li/' + btn.data('id') + '/'; 
    if (btn.data('state') == 'closed') {
        $.ajax({                    
            url: request,
            method: "GET",            
            success: function(result){
                if (result.slice(0,5) == 'Error') {
                    if (btn.attr('id') != 'expand_root') {
                        alert(result);     
                    }                                       
                } else {
                    parent.append(result);
                };
            },
            error: function(result){ 
                alert(result);               
            }

        });
        btn.data('state', 'open');     
    } else {
        li_to_remove = $("li", $(parent));
        li_to_remove.remove();
        btn.data('state', 'closed');  
    };
};

$('a.insert_btn').on("click", function(e){
    //Insert button in admin_menu pressed
    var a = $(this);
    var child_chbox = $('input#child_checkbox');
    $('span#change_menu_entry_id').text(a.data('id'));        
    $('div#change_menu').toggleClass('invisible', false);
    if (Boolean(a.data('iscategory'))) {
        child_chbox.toggleClass('invisible', false);
        child_chbox.prop('checked', true);
    } else {
        child_chbox.toggleClass('invisible', true); 
        child_chbox.prop('checked', false); 
    };
});

$('button#change_insert_btn').on("click", function(e){
    //Insert button on modification menu pressed
    var btn = $(this);
    var request = ''        
    category_id = getCategory();
    product_id = getProduct();
    create_child = getChildCheckbox();
    create_category = getCategoryRadio();

    if (create_child) {
        request += '/insch/';
    } else {
        request += '/inssib/';
    };

    request += $('span#change_menu_entry_id').text() + '/';

    if (create_category) {
        if (!category_id) {
            alert('Category is not set');
            return;
        }
        request += '1/' + category_id + '/';            
    } else {
        if (!product_id) {
            alert('Product is not set');
            return;
        }
        request += '0/' + product_id + '/';
    };
    $.ajax({                    
        url: request,
        method: "GET",
        success: function(result){
            if (result.slice(0,5) == 'Error') {
                alert(result);
            } else {
                location.reload();
            };
        },
        error: function(result){ 
            alert(result);               
        }
    });         
    $('div#change_menu').toggleClass('invisible', true);
});

$(document).ready(function(){ 

    //Expands root element
    var btn = $('a#expand_root');
    expand_pressed(btn);
});
