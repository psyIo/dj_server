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
        console.debug('rastas produktas ' + match.data('id')); //dev
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

$(document).ready(function(){ 

    $('a.insert_btn').on("click", function(e){
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
        console.log(request);
        $.ajax({                    
            url: request,
            method: "GET",
            // data: {'last_msg_dt' : $('#last_msg_on').html(),
            //        'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()}, 
  
            success: function(result){
                if (result.slice(0,5) == 'Error') {
                    alert(request);
                } else {
                    location.reload();
                };
                console.log('ajax call success: ' + result); 
            },
            error: function(result){                
                console.log('ajax call error: ', + result);
            }
        });         
        $('div#change_menu').toggleClass('invisible', true);
    });

});
