odoo.define('myevo_web.profile_menu_custom', function (require) {
"use strict";  
var core = require('web.core');
var Dialog = require('web.Dialog');
var framework = require('web.framework');
var Model = require('web.DataModel');
var session = require('web.session');
var Widget = require('web.Widget');
var ActionManager = require('web.ActionManager');
var core = require('web.core');
var _t = core._t;
var QWeb = core.qweb;
var UserMenu = require('web.UserMenu');

	UserMenu.include({
		 on_menu_profile: function () {
			 var self = this;
		     this.getParent().clear_uncommitted_changes().then(function() {
		    	 var profile = new Model('user.profile');

		         self.rpc("/web/action/load", { action_id: "soupese_base.action_menu_profile_user" }).done(function(result) {
		            // result.res_id = session.uid;		        	 
		             self.getParent().action_manager.do_action(result);
		         });
		     });
		 },
	});
});


