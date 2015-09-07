(function ($) {

  vac_templater.commands = vac_templater.commands || {};

  /******************************************************************************
   * REDIRECT.
   ******************************************************************************/

  vac_templater.commands.redirect = function(url) {
    window.location = url;
    return true;
  };

  /******************************************************************************
   * CHECK VERSION.
   ******************************************************************************/

  vac_templater.commands.check_version = function(version) {
    if ((version.js.major != vac_templater.version.js.major) || (version.css.major != vac_templater.version.css.major)) {
      window.location.reload();
      return true;
    }
  };

  /******************************************************************************
   * SET CONTENT.
   ******************************************************************************/

  vac_templater.commands.set_content = function(contents) {
    // Detach behaviors.
    vac_templater.detach_behaviors('#content');

    // Update container.
    $('#content').html(contents);

    // Attach behaviors.
    vac_templater.attach_behaviors('#content');
  };

  /******************************************************************************
   * DOWNLOAD.
   ******************************************************************************/

  vac_templater.commands.download = function(url) {
    window.location = url;
  };

  /******************************************************************************
   * ALERT.
   ******************************************************************************/

  vac_templater.commands.alert = function(message) {
    alert(message);
  };

  /******************************************************************************
   * PROGRESS.
   ******************************************************************************/

  (function () {

    var next_ping_timer = null;
    var next_increment_timer = null;

    function enqueue_next_ping(url, timeout) {
      next_ping_timer = setTimeout(function() {
        vac_templater.ajax.call({
          type: 'GET',
          url: url,
          error: function(xhr, status) {
            // Retry again unless the request has been explicitly aborted.
            if (!xhr.vac_templater.is_aborted(status)) {
              enqueue_next_ping(url, timeout);
            }
          }
        });
      }, timeout);
    }

    function enqueue_next_increment(bar, n, inc, timeout) {
      if (n > 0) {
        next_increment_timer = setTimeout(function() {
          var value = parseFloat($(bar).attr('data-value')) + inc;
          if (value <= (bar).attr('data-max')) {
            $(bar).attr('data-value', value).css('width', value + '%');
            enqueue_next_increment(bar, n-1, inc, timeout);
          }
        }, timeout);
      }
    }

    vac_templater.commands.show_progress = function(progress_url, cancel_url, timeout, title) {
      // Build progress modal.
      var modal = $(
        '<div class="modal fade" id="progress-modal" data-url="' + progress_url + '">' +
        '  <div class="modal-dialog">' +
        '    <div class="modal-content">' +
        '      <div class="modal-header">' +
        '        <h3>' + title + '</h3>' +
        '      </div>' +
        '      <div class="modal-body">' +
        '        <div class="progress progress-striped active" style="display: none;">' +
        '          <div class="progress-bar" data-max="0" data-value="0" style="width: 0%;"></div>' +
        '        </div>' +
        '        <p class="pull-right"><i class="glyphicon glyphicon-warning-sign"></i> ' + gettext('Please, be patient. <strong>Do not close or reload the page!</strong>') + '</p>' +
        '      </div>' +
        '      <div class="modal-footer">' +
        '        <a href="#" class="btn btn-danger"><i class="glyphicon glyphicon-remove glyphicon-white"></i> ' + gettext('Abort') + '</a>' +
        '      </div>' +
        '    </div>' +
        '  </div>' +
        '</div>');

      // Bind cancel button event.
      $('.modal-footer .btn', modal).click(function() {
        // Locally flag as aborted and clear any currently active interval.
        clearInterval(next_ping_timer);
        clearInterval(next_increment_timer);

        // Make an AJAX call to cancel the task also in the server.
        vac_templater.ajax.call({
          url: cancel_url,
          type: 'POST',
          element: this
        });
        return false;
      });

      // Open progress modal.
      vac_templater.modal.open(modal);

      // Enqueue next progress update.
      enqueue_next_ping(progress_url, timeout);
    };

    vac_templater.commands.update_progress = function(value, timeout) {
      // Fetch progress modal.
      modal = $('#progress-modal');
      if (modal.length > 0) {
        // Update value (if any)
        if (value) {
          // Display progress bar.
          $(modal).find('.progress').show();

          // Render small increments every 100ms until next expected ping.
          var bar = $(modal).find('.progress-bar');
          var diff = value - $(bar).attr('data-max');
          if (diff > 0) {
            $(bar).attr('data-max', value);
            var nupdates = Math.ceil(timeout/100);
            enqueue_next_increment(bar, nupdates, diff/nupdates, 100);
          }
        }

        // Enqueue next progress update.
        enqueue_next_ping($(modal).attr('data-url'), timeout);
      }
    };

    vac_templater.commands.hide_progress = function() {
      modal = $('#progress-modal');
      if (modal.length > 0) {
        $(modal).modal('hide');
      }
    };
  })();

  /******************************************************************************
   * MODAL & CLOSE_MODAL.
   ******************************************************************************/

  vac_templater.commands.modal = function(contents) {
    // Append any included script tags to the document so they get
    // executed.
    $(contents).filter('script').appendTo('body');

    // Sanity check: Modal contents must consist of a single
    // element with the class modal.
    var modal = $(contents).filter('.modal');
    if (modal.length == 1) {
      vac_templater.modal.open(modal);
    }
  };

  vac_templater.commands.close_modal = function() {
    vac_templater.modal.close_all();
  };

  /******************************************************************************
   * NOTIFY.
   ******************************************************************************/

  vac_templater.commands.notify = function(messages) {
    if (messages.length > 0) {
      // Find and clean up target 'inline-notifications-container' DOM element (if any).
      var container = $('.inline-notifications-container').last().html('');

      // Process inline notifications.
      var is_inline = function(message) {
        return ((message.tags.indexOf('inline') != -1) && ($(container).length > 0));
      };
      var inline_messages = $.grep(messages, is_inline);
      $.each(inline_messages, function() {
        vac_templater.notifications.notify(this.type, this.message, null, container);
      });

      // Process cool & floating notifications.
      var other_messages = $.grep(messages, is_inline, true);
      $.each(other_messages, function() {
        var expires = null;
        if ((this.type != 'error')) {
          expires = 5000 + 100 * this.message.length;
        }
        vac_templater.notifications.notify(this.type, this.message, expires, (other_messages.length > 1) ? 'floating' : 'cool');
      });
    }
  };

})(jQuery);
