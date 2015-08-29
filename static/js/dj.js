// =======================
//question_detail
//открывает-закрывает комментарии
$(function(){
$(".dropdown-comment-container").hide();
$("a.dropdown-comment-link").click(function(e) {
    e.preventDefault();

    var $div = $(this).next('.dropdown-comment-container');
    $(".dropdown-comment-container").not($div).hide();

    if ($div.is(":visible")) {
        $div.hide();
    }  else {
        $div.show();
    }

    if ($('.dropdown-comment-container:visible')){
       $('.dropdown-comment-container:visible').prev($("a.dropdown-comment-link")).text('скрыть');
       $('.dropdown-comment-container:hidden').prev($("a.dropdown-comment-link")).text('добавить комментарий');
     }
});

//$(document).click(function(){
//позволяет закрывать комменты кликом по любому месту страницы
//var p = $(e.target).closest('.dropdown').length
//if (!p) {
//$(".dropdown-container").hide();
//}
//конец позволяет закрывать комменты кликом по любому месту страницы

//});
});
//конец открывает-закрывает комментарии







// =======================
//studyset_detail
//открывает-закрывает комментарии
$(function(){

$("a.dropdown-link").click(function(e) {
    e.preventDefault();

    var $div = $(this).next('.dropdown-container');
    $(".dropdown-container").not($div).hide();

    if ($div.is(":visible")) {
        $div.hide();
    }  else {
        $div.show();
    }

    if ($('.dropdown-container:visible')){
       $('.dropdown-container:visible').prev($("a.dropdown-link")).text('скрыть');
       $('.dropdown-container:hidden').prev($("a.dropdown-link")).text('ответить');
     }

});

//$(document).click(function(){
//позволяет закрывать комменты кликом по любому месту страницы
//var p = $(e.target).closest('.dropdown').length
//if (!p) {
//$(".dropdown-container").hide();
//}
//конец позволяет закрывать комменты кликом по любому месту страницы

//});
});
//конец открывает-закрывает комментарии



/*
//table pagination
// =======================
$(function()  {

$('table.paginated').each(function() {
    var currentPage = 0;
    var numPerPage = 1;
    var $table = $(this);
    $table.bind('repaginate', function() {
        $table.find('tbody tr').hide().slice(currentPage * numPerPage, (currentPage + 1) * numPerPage).show();
    });
    $table.trigger('repaginate');
    var numRows = $table.find('tbody tr').length;
    var numPages = Math.ceil(numRows / numPerPage);
    var $pager = $('<ul class="pagination"></ul>');


    for (var page = 0; page < numPages; page++) {
        $('<a href="#" class="page-number"></a>').text(page + 1).bind('click', {
            newPage: page
        }, function(event) {
            event.preventDefault();
            currentPage = event.data['newPage'];
            $table.trigger('repaginate');
            $(this).parent().addClass('active').siblings().removeClass('active');
        }).appendTo($pager).addClass('clickable');
    }

    $pager.insertAfter($table);
});

    $('.page-number').wrap('<li class="pag"></li>');

    $('.pag').eq(0).addClass('active');

});
*/

//ajax search (for tags)
// =======================

$(function(){
    $('#search_tag').keyup(function() {
        $.ajax({
            type: "POST",
            url: "/search_tags/",
            data: {
                'search_text' : $('#search_tag').val(),
                'csrfmiddlewaretoken' : $("input[name=csrfmiddlewaretoken]").val()
            },
            success: searchSuccess,
            dataType: 'html'

        });
    });
});

function searchSuccess(data, textStatus, jqXHR)
{

    $('#search-tag-results').html(data);

}



//ajax search (for users)
// =======================

$(function(){
    $('#search_user').keyup(function() {
        $.ajax({
            type: "POST",
            url: "/search_users/",
            data: {
                'search_text' : $('#search_user').val(),
                'csrfmiddlewaretoken' : $("input[name=csrfmiddlewaretoken]").val()
            },
            success: searchUserSuccess,



            dataType: 'html'


        });
    });
});

function searchUserSuccess(data, textStatus, jqXHR)
{

    $('#search-user-results').html(data);

}

//studyset_list
//ajax иконка сохранения статьи, по клику на иконке  сохраняет статью, меняет стиль, меняет атрибуты, меняет число сохранённых статей
// =======================
$(function() {
 $("#dialog_save_studyset").dialog({
  	autoOpen: false,
    width:400,
    height: 55,
    position: [900, 25]

  });
$('.save_studyset_link').click( function(e) {
e.preventDefault();
var studyset_slug = $(this).next('.foo2').text();
var studyset_id = $(this).prev('.foo').text();
var save_studyset = $('#save_studyset_' + studyset_id);
var count = Number($('#count_' + studyset_id ).text());
$.ajax({
          url: '/studysets/studyset/'+ studyset_slug + '/save/',
          success:function(data) {
          save_studyset.toggleClass('glyphicon-star-empty glyphicon-star favorite-color icon-color');
          save_studyset.hasClass("favorite-color")?  count +=  1 :  count -= 1;
          $('#count_' + studyset_id).text(count);
              console.log(count)
          save_studyset.hasClass("favorite-color")? save_studyset.attr("title", "Эта тема уже в избранном. Кликнете чтобы удалить.") :
          save_studyset.attr("title", "Добавить в избранное");
          $("#dialog_save_studyset").dialog("open");
          setTimeout("$('#dialog_save_studyset').dialog('close')",3000);
            save_studyset.hasClass("favorite-color")? $('#studyset_dialog_text').text('добавлена в избранное') :
          $('#studyset_dialog_text').text('удалена из избранного');
          }
 });
});
});


//конец ajax кнопка сохранения статьи






