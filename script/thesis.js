$(document).ready(function(){
    $(".thesis").hide();
});

$(document).ready(function(){
    $('section nav li:nth-of-type(1)').addClass('nav-hover'); 
});
  
$(function($) {
    $('nav li').click(function() {
        $('section:nth-of-type('+$(this).data('rel')+')').show().siblings('section').hide(); 
        

        $('section nav li:nth-of-type('+$(this).data('rel')+')').addClass('nav-hover').siblings().removeClass('nav-hover');
    });
  })(jQuery);

