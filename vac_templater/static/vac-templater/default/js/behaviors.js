(function ($) {

  vac_templater.behaviors = vac_templater.behaviors || {};

  /******************************************************************************
   * AJAX FORM.
   ******************************************************************************/

  vac_templater.behaviors.form = {
    attach: function(context) {
      function complete(form, wait) {
        $(form)
          .find('input[name=_iframe_upload]').remove().end()
          .find(':input').removeAttr('disabled').end()
          .find('input[type=submit], button[type=submit]').removeClass('ajaxing').end()
          .removeClass('ajaxing');
        if (!wait) {
          $(form).stop(true, true).css('opacity', 1.0);
        }
      }

      $('form.ajax', context).once('ajax-form').each(function () {
        var form = this;
        var options = {
          url: $(this).attr('action'),
          data: { csrfmiddlewaretoken: vac_templater.csrf_token },
          beforeSerialize: function(form, options) {
            if (options.iframe) {
              // See http://jquery.malsup.com/form/#file-upload. Used in server side
              // to identify 'fake' AJAX requests.
              $(form).append('<input type="hidden" name="_iframe_upload" value="1"/>');
            }
          },
          beforeSubmit: function(arr, form, options) {
            vac_templater.notifications.close_all();
            $(form)
              .find(':input').attr('disabled', true).end()
              .find('input[type=submit], button[type=submit]').addClass('ajaxing').end()
              .addClass('ajaxing')
              .animate({opacity: 0.2}, 200);
          },
          success: function(response, status, xhr, form) {
            var wait = vac_templater.execute_commands(response, form, {});
            complete(form, wait);
          },
          error: function(xhr, status) {
            if ((typeof xhr.vac_templater == 'undefined') || (!xhr.vac_templater.is_aborted())) {
              vac_templater.notifications.notify(
                'error',
                gettext("We are sorry, but the request couldn't be processed. Please, try again later."));
            }
            if ((typeof xhr.vac_templater == 'undefined') || (!xhr.vac_templater.aborted_by_same_category)) {
              complete(form, false);
            }
          },
          type: ($(this).attr('method') || 'POST').toUpperCase(),
          dataType: 'json',
          iframe: false
        };
        $(form).ajaxForm(options);
      });
    }
  };

  /******************************************************************************
   * AJAX LINK.
   ******************************************************************************/

  vac_templater.behaviors.link = {
    attach: function(context) {
      $('a.ajax', context).once('ajax-link').click(function(event) {
        if ($(this).is(':not(.disabled)')) {
          var url = $(this).attr('href');
          var type = ($(this).data('method') || 'GET').toUpperCase();
          vac_templater.ajax.call({
            url: url,
            type: type,
            element: this
          });
          event.preventDefault();
        }
      });
    }
  };

  /******************************************************************************
   * CONFIRMATION DIALOG.
   ******************************************************************************/

  vac_templater.behaviors.confirm = {
    attach: function(context) {
      $('a.confirm', context).once('confirm').each(function() {
        // Bind a click handler to show the confirmation modal.
        $(this).bind('click.confirm', function (event) {
          target = $(this);
          // Check if the action has already been confirmed.
          if (!target.data('confirmed')) {
            // Still not confirmed.
            // Extract options and set defaults.
            var title = target.data('title') || gettext('Are you sure?');
            var text = target.data('text') || gettext("This action can't be undone.");
            var cancel_button = target.data('cancel-button') || gettext('Cancel');
            var confirm_button = target.data('confirm-button') || gettext('Yes');

            // Open confirmation modal.
            vac_templater.modal.open($(
              '<div class="modal fade" role="dialog">' +
              '  <div class="modal-dialog" role="document">' +
              '    <div class="modal-content">' +
              '      <div class="modal-header">' +
              '        <h3>' + title + '</h3>' +
              '      </div>' +
              '      <div class="modal-body">' + text + '</div>' +
              '      <div class="modal-footer">' +
              '        <a href="#" class="btn" data-dismiss="modal"><i class="glyphicon glyphicon-remove"></i> ' + cancel_button + '</a>' +
              '        <a href="#" class="btn btn-danger btn-confirm" data-dismiss="modal"><i class="glyphicon glyphicon-ok glyphicon-white"></i> ' + confirm_button + '</a>' +
              '      </div>' +
              '    </div>' +
              '  </div>' +
              '</div>').find('.btn-confirm').click(function (event) {
                // A click on the confirmation button will confirm the
                // action and launch the original click event again.
                event.preventDefault();
                target.data('confirmed', true).click();
              }).end());

            // Keep other handlers from executing.
            event.stopImmediatePropagation();
            event.preventDefault();
          } else {
            // Action has been confirmed. Let other handlers execute, but
            // first remove confirmation flag so that further clicks require
            // a new confirmation.
            target.data('confirmed', false);
          }
        });

        // We must ensure this click handler gets called first. The method
        // used for it has a dependency on an internal jQuery data structure,
        // so check it actually exists (as it may change on a library update).
        var handlers = $._data(this, "events");
        if (typeof handlers != 'undefined') {
          // If there are more handlers, move the new one to the top of the list.
          if (handlers.click.length > 1) {
            handlers.click.unshift(handlers.click.pop());
          }
        } else {
          // No jQuery support for data('events'). Unbind the click event as
          // we can't ensure it will work.
          $(this).unbind('click.confirm');
        }
      });
    }
  };

  /******************************************************************************
   * BOOTSTRAP.
   ******************************************************************************/

  vac_templater.behaviors.bootstrap = {
    attach: function(context) {
      // Popovers.
      $('[data-toggle="popover"]', context).popover({
        trigger: 'hover',
        delay: { show: 500, hide: 100 }
      });

      // Tooltips.
      $('[data-toggle="tooltip"]', context).tooltip();
    }
  };

  /******************************************************************************
   * SELECT2.
   ******************************************************************************/

  vac_templater.behaviors.select2 = {
    attach: function(context) {
      $('select', context).select2({
        width: 'resolve',
        language: {
          errorLoading: function () {
            return gettext('The results could not be loaded.');
          },
          inputTooLong: function (args) {
            var overChars = args.input.length - args.maximum;
            var fmts = ngettext(
              'Please delete %s character',
              'Please delete %s characters', overChars);
            return interpolate(fmts, [overChars]);
          },
          inputTooShort: function (args) {
            var remainingChars = args.minimum - args.input.length;
            var fmts = ngettext(
              'Please enter %s more character',
              'Please enter %s more characters', remainingChars);
            return interpolate(fmts, [remainingChars]);
          },
          loadingMore: function () {
            return gettext('Loading more results...');
          },
          maximumSelected: function (args) {
            var fmts = ngettext(
              'You can only select %s item',
              'You can only select %s items', args.maximum);
            return interpolate(fmts, [args.maximum]);
          },
          noResults: function () {
            return gettext('No results found');
          },
          searching: function () {
            return gettext('Searching...');
          }
        }
      });
    }
  };

  /******************************************************************************
   * FIXED SIDEBAR.
   ******************************************************************************/

  (function () {
    var item_height = 76;
    var collapsed_padding = 60;

    // Fix bar.
    function adjust_position(sidebar) {
      $(sidebar).css({
        'top': $('#content').offset().top,
        'left': $('#content').offset().left,
        'position': 'fixed'
      });
    }

    // Add/remove 'more' button.
    function adjust_items(sidebar) {
      // Fetch more button. Stop if not found.
      var more = $(sidebar).find('li.more');
      if (more.length > 0) {
        // Reset collapsed.
        var collapsed = $(sidebar).parent().find('> .collapsed');
        $(collapsed).fadeOut().data({is_visible: false});

        // Get current sidebar length & max length.
        var current_length = $(sidebar).find('.nav li').length;
        var max_length = Math.round(($(sidebar).innerHeight() - 80) / item_height);
        if (max_length < 2 ) {
          max_length = 2;
        }

        // Adjust.
        if (current_length > max_length) {
          pop_item(sidebar, collapsed, current_length - max_length);
        } else {
          push_item(sidebar, collapsed, max_length - current_length);
        }
        $(more).toggle($(collapsed).find('.nav li').length > 0);
      }
    }

    function pop_item(sidebar, collapsed, n) {
      // Do not pop item from sidebard in case the collapsed menu
      // will only contain one item.
      if ((n > 1) || ($(collapsed).find('.nav li').length > 0)) {
        var lis = $(sidebar).find('.nav li');
        var nav = $(collapsed).find('.nav');
        for(var i = lis.length - 2, j = 0; j < n; i--, j++) {
          $(nav).prepend(lis[i]);
        }
      }
    }

    function push_item(sidebar, collapsed, n) {
      // If after pushing to sidebar, collapsed menu will only contain
      // one item ==> push all collapsed items back to the sidebar.
      if ($(collapsed).find('.nav li').length - n === 1) {
        n += 1;
      }
      // Do it!
      var lis = $(collapsed).find('.nav li');
      var more = $(sidebar).find('li.more');
      for(var i = 0, j = 0; j < n; i++, j++) {
        more.before(lis[i]);
      }
    }

    vac_templater.behaviors.fixed_sidebar = {
      attach: function(context) {
        $('.sidebar', context).once('sidebar').each(function() {
          var sidebar = this;

          // Add collapsed items container.
          $(sidebar).after(
            '<div class="collapsed">' +
            '  <div class="arrow"></div>' +
            '  <ul class="nav nav-pills"></ul>' +
            '</div>'
          );

          // Set position & adjust items.
          adjust_position(sidebar);
          adjust_items(sidebar);

          // Button 'more' click event.
          $(sidebar).find('li.more a').bind('click', function(e) {
            e.preventDefault();
            var collapsed = $(this).parents('.sidebar').parent().find('> .collapsed');
            if ($(collapsed).find('.nav li').length > 0) {
              if ($(collapsed).data('is_visible') !== undefined && $(collapsed).data('is_visible')) {
                $(collapsed).data({is_visible: false});
                $(collapsed).fadeOut();
              } else {
                $(collapsed).data({is_visible: true});
                var offset = $(this).find('.glyphicon').offset();
                $(collapsed).css({
                  'top': offset.top - 15 - window.scrollY + 'px',
                  'left': offset.left + collapsed_padding + 'px'
                }).fadeIn();
              }
            }
          });

          if ($('body').once('sidebar').length > 0) {
            $(window).resize(function() {
              var sidebar = $('.sidebar', context);
              if (sidebar.length > 0) {
                adjust_position(sidebar);
                adjust_items(sidebar);
              }
            });
          }
        });
      }
    };
  })();

  /******************************************************************************
   * DATETIME INPUT.
   ******************************************************************************/

  (function () {
    // Transform datetime strftm format used in Django to the format used by
    // Moment.js (and therefore, by Bootstrap Datetimepicker).
    // See https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
    // See http://momentjs.com/docs/#/displaying/format/
    var replacements = {
      a: 'ddd',
      A: 'dddd',
      b: 'MMM',
      B: 'MMMM',
      d: 'DD',
      e: 'D',
      F: 'YYYY-MM-DD',
      H: 'HH',
      I: 'hh',
      j: 'DDDD',
      k: 'H',
      l: 'h',
      m: 'MM',
      M: 'mm',
      p: 'A',
      S: 'ss',
      u: 'E',
      w: 'd',
      W: 'WW',
      y: 'YY',
      Y: 'YYYY',
      z: 'ZZ',
      Z: 'z',
      '%': '%'
    };

    var format = vac_templater.datetime_format.replace(
      new RegExp(Object.keys(replacements).map(function(val) {
        return '%' + val; }).join('|'), 'g'),
      function myFunction(val) {
        return replacements[val.substring(1)];
      });

    vac_templater.behaviors.datetime_input = {
      attach: function(context) {
        // Transform every datetime input into a Datetimepicker-enhanced input.
        $('.datetime-input').datetimepicker({
          format: format
        });
      }
    };
  })();

  /******************************************************************************
   * REPEATABLE FIELD.
   ******************************************************************************/

  vac_templater.behaviors.repeatable_field = {
    attach: function(context) {
      $('.repeatable-field').once('repeatable-field').each(function() {
        var repeatable_fields = this;
        var button = $('<button type="button" class="form-control btn btn-default"><i class="glyphicon glyphicon-plus"></i></button>').click(function() {
          var last_input = $(repeatable_fields).find(':input:not("button"):last');
          var id_match = last_input.attr('id').match(/(.*)_(\d+)$/);
          var new_id = id_match[1] + '_' + (parseInt(id_match[2]) + 1);
          var name_match = last_input.attr('name').match(/(.*)_(\d+)$/);
          var new_name = name_match[1] + '_' + (parseInt(name_match[2]) + 1);
          var new_input = last_input.clone().val(null).attr('id', new_id).attr('name', new_name);
          last_input.after(new_input);
        });
        $(this).append(button);
      });
    }
  };

})(jQuery);
