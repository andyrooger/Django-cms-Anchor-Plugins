jQuery(document).ready(function(){
  jQuery(".toc").each(function(){
    if(jQuery(this).data("toc") === null)
      setupToC(jQuery(this));
  });
});

function setupToC(toc){
  toc.find(".item").each(function(){
    if(jQuery(this).children(".collapsible").length != 0){
      jQuery(this).children(".manipulator")
        .click(function(){
          jQuery(this).parent().toggleClass("closed");
        }).css("display","inline-block");
    }
  });

  toc.data("toc", true);
}
