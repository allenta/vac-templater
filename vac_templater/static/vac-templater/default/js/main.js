(function ($) {

  vac_templater.serial = vac_templater.serial || 0;
  vac_templater.overlay_handlers = vac_templater.overlay_handlers || [];

  /******************************************************************************
   * BEHAVIORS.
   ******************************************************************************/

  vac_templater.attach_behaviors = function(context) {
    context = context || document;
    $.each(vac_templater.behaviors, function() {
      if ($.isFunction(this.attach)) {
        this.attach(context);
      }
    });
  };

  vac_templater.detach_behaviors = function(context) {
    context = context || document;
    $.each(vac_templater.behaviors, function() {
      if ($.isFunction(this.detach)) {
        this.detach(context);
      }
    });
  };

  /******************************************************************************
   * COMMANDS.
   ******************************************************************************/

  vac_templater.execute_commands = function(commands, context, library) {
    context = context || this;
    library = $.extend({}, vac_templater.commands, library);
    commands.sort(function(a, b) {
      return a.weight - b.weight;
    });
    var wait = false;
    for (var i in commands) {
      if (commands[i]['cmd'] && commands[i]['args'] && library[commands[i]['cmd']]) {
        wait = library[commands[i]['cmd']].apply(context, commands[i]['args']) || wait;
      }
    }
    return wait;
  };

  /******************************************************************************
   * READY.
   ******************************************************************************/

  vac_templater.ready = function(callback, is_ready, unloader) {
    function execute(callback, is_ready, unloader, context) {
      if ((typeof(is_ready) == 'function') && (is_ready() === false)) {
        // is_ready defined and not yet fulfilled. Try again in 100 ms.
        window.setTimeout(function() { execute(callback, is_ready, unloader, context); }, 100);
      } else {
        // Execute callback.
        if (vac_templater.client.browser.ie >= 1 && vac_templater.client.browser.ie <= 9) {
          callback($(document));
        } else {
          callback(context);
        }
        // Add unload behaviour.
        if (typeof(unloader) == 'function') {
          vac_templater.unload(unloader(context));
        }
      }
    }

    if (!vac_templater.behaviors.ready) {
      vac_templater.behaviors.ready = {
        callbacks: [],
        attach: function(context) {
          $(document).ready(function() {
            var callbacks = vac_templater.behaviors.ready.callbacks;
            delete vac_templater.behaviors.ready;
            for (var i = 0; i < callbacks.length; i++) {
              execute(callbacks[i]['callback'], callbacks[i]['is_ready'], callbacks[i]['unloader'], context);
            }
          });
        }
      };
    }

    vac_templater.behaviors.ready.callbacks.push({
      callback: callback,
      is_ready: is_ready,
      unloader: unloader
    });
  };

  vac_templater.unload = function(callback) {
    if (!vac_templater.behaviors.unload) {
      vac_templater.behaviors.unload = {
        callbacks: [],
        attach: function(context) {
          // Nothing to do here.
        },
        detach: function(context) {
          for (var i = 0; i < vac_templater.behaviors.unload.callbacks.length; i++) {
            var callback = vac_templater.behaviors.unload.callbacks[i];
            if (callback(context)) {
              vac_templater.behaviors.unload.callbacks.splice(i, 1);
              i--;
            }
          }
          if (vac_templater.behaviors.unload.callbacks.length === 0) {
            delete vac_templater.behaviors.unload;
          }
        }
      };
    }
    vac_templater.behaviors.unload.callbacks.push(callback);
  };

  /******************************************************************************
   * MODAL.
   ******************************************************************************/

  /**
   *
   */
  vac_templater.modal = {
    open: function(modal) {
      // Hide all previous modals.
      vac_templater.modal.close_all();
      // Append new modal in the overlay area.
      $('#overlay').append(modal);
      // Attach behaviors.
      // show() method called before attaching behaviors is required to ensure
      // behaviors can access final width of elements.
      vac_templater.attach_behaviors(modal.show());
      // On close, detach behaviors & self-destroy modal.
      modal.on('hidden.bs.modal', function () {
        vac_templater.detach_behaviors(this);
        $(this).remove();
      });
      // Done!
      modal.modal('show');
    },
    close_all: function() {
      $('#overlay .modal').modal('hide');
    }
  };

  /******************************************************************************
   * GENERAL UTILITY STUFF.
   ******************************************************************************/

  /**
   *
   */
  vac_templater.register_overlay_handler = function(id, callback) {
    vac_templater.overlay_handlers[id] = callback;
  };

  /**
   *
   */
  vac_templater.close_all_overlays = function() {
    for (var id in vac_templater.overlay_handlers) {
      (vac_templater.overlay_handlers[id])();
    }
  };

  /******************************************************************************
   * JQUERY EXTENSIONS.
   ******************************************************************************/

  /**
   *
   */
  $.fn.toggleAttr = function(name, value1, value2) {
    var value = value1;
    if ($(this).attr(name) == value1) {
      value = value2;
    }
    return $(this).attr(name, value);
  };

  /******************************************************************************
   * DOCUMENT LEVEL INITIALIZATIONS.
   ******************************************************************************/

  $(document).ready(function() {
    // Register document level overlay handlers.
    vac_templater.register_overlay_handler('notifications', vac_templater.notifications.close_all);
    vac_templater.register_overlay_handler('modals', function() { vac_templater.modal.close_all(); });
    vac_templater.register_overlay_handler('tooltips', function() { $('[data-toggle="tooltip"]').tooltip('hide'); });
    vac_templater.register_overlay_handler('popovers', function() { $('[data-toggle="popover"]').popover('hide'); });
    vac_templater.register_overlay_handler('dropdowns', function() { $('.dropdown, .dropup').removeClass('open'); });
    vac_templater.register_overlay_handler('btn-groups', function() { $('.btn-group').removeClass('open'); });

    // Attach all behaviors.
    vac_templater.attach_behaviors(this);

    // Initialize notifications container.
    $('#floating-notifications-container').notify({
      speed: 300,
      expires: 7000,
      stack: 'above'
    });

    // iPad & iPhone hacks.
    if (vac_templater.client.system.ipad || vac_templater.client.system.iphone) {
      $('body').on('touchstart.dropdown', '.dropdown-menu', function (e) { e.stopPropagation(); });
    }
  });

})(jQuery);
