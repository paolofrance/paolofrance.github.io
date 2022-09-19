
$(function(){
    $("#header").load("header.html"); 
});

$(function(){
    $("#bottoni").load("bottoni.html"); 
});

$(function(){
    $("#social").load("social.html"); 
});


$(function($) {
    $('nav li').click(function() {
      $('section:nth-of-type('+$(this).data('rel')+')').stop().fadeIn(1, 'linear').siblings('section').stop().fadeOut(1, 'linear'); 
    });
  })(jQuery);
