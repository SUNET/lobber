function _i(message) {
   $('#notification').jnotifyAddMessage({
       text: message,
       permanent: false,
       type: 'info'
   });
}
function _e(message) {
   $('#notification').jnotifyAddMessage({
       text: message,
       permanent: true,
       type: 'error'
   });
}
function getDialogButton( dialog_selector, button_name )
{
  var buttons = $( dialog_selector + ' .ui-dialog-buttonpane button' );
  for ( var i = 0; i < buttons.length; ++i )
  {
     var jButton = $( buttons[i] );
     if ( jButton.text() == button_name )
     {
         return jButton;
     }
  }

  return null;
}
$(function() {
   $("input:submit, input:button").button();
   $("a",".button").button();
   $('#notification').jnotifyInizialize({
      oneAtTime: false,
      appendType: 'append'
   }).css({
      'font-size': "120%",
      'position': 'absolute',
      'marginTop': '20px',
      'padding': '15px',
      'right': '20px',
      'width': '250px',
      'z-index': '9999'
   });
   $('.tip').tooltip({showURL: false});
   /**
   stomp = new STOMPClient();
   stomp.onopen = function() {
       if (debug) {
          _i("STOMP connection opened");
	   }
   };
   stomp.onclose = function(c) { 
       if (debug) {
	       _e("STOMP connection lost: "+c);
	   }
   };
   stomp.onerror = function(error) {
   	   _e(error);
   };
   stomp.onerrorframe = function(frame) {
       _e(frame.body);
   };
   stomp.onconnectedframe = function() {
       stomp.subscribe("/session/"+$.cookie("sessionid"));
   };
   stomp.onmessageframe = function(frame) {
       _i(frame.body);
   };
   stomp.connect(stomp_host,stomp_port);
   **/
});