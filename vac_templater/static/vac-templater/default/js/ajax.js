(function ($) {

  var ajaxers = [];

  vac_templater.ajax = vac_templater.ajax || {};

  $.ajaxSetup({
    cache: false,
    traditional: true
  });

  vac_templater.ajax.call = function(options) {
    // Init options.
    options.type = options.type || 'POST';
    options.category = options.category || null;
    options.context = options.context || $(document);
    options.element = options.element || null;
    options.data = options.data || {};
    options.commands = options.commands || {};
    options.before_send = options.before_send || null;
    options.complete = options.complete || null;
    options.success = options.success || null;
    options.error = options.error || null;

    // Do it!
    $.ajax({
      url: options.url,
      data: options.data,
      type: options.type,
      dataType: 'json',
      beforeSend: function(xhr, settings) {
        var result = true;
        xhr.vac_templater = {
          weight: 100
        };
        if (options.before_send) {
          result = options.before_send(xhr, settings);
        }
        if (result && options.element) {
          $(options.element).addClass('ajaxing');
        }
        return result;
      },
      complete: options.complete,
      success: function(response, status, xhr) {
        $(options.element).removeClass('ajaxing');
        var wait = vac_templater.execute_commands(response, options.context, options.commands);
        if (options.success) {
          options.success(response, status, xhr, wait);
        }
      },
      error: function(xhr, status, error) {
        if (!xhr.vac_templater.is_aborted(status)) {
          vac_templater.notifications.notify(
            'error',
            gettext("We are sorry, but the request couldn't be processed. Please, try again later."));
        }
        if (!xhr.vac_templater.aborted_by_same_category) {
          $(options.element).removeClass('ajaxing');
        }
        if (options.error) {
          options.error(xhr, status);
        }
      }
    });
  };

  $(document).ajaxSend(function(event, xhr, settings) {
    function same_origin(url) {
      // URL could be relative or scheme relative or absolute.
      var host = document.location.host; // host + port
      var protocol = document.location.protocol;
      var sr_origin = '//' + host;
      var origin = protocol + sr_origin;
      // Allow absolute or scheme relative URLs to same origin.
      return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
    }

    function safe_method(method) {
      return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    // Add/extend vac_templater stuff for xhr instance.
    var data = {
      id: vac_templater.serial++,
      weight: 100
    };
    $.extend(data, xhr.vac_templater || {});
    xhr.vac_templater = data;
    xhr.vac_templater.category = settings.category || settings.url;
    xhr.vac_templater.is_aborted = function(status) {
      return (xhr.aborted || (status == 'abort') || (status == 'aborted'));
    };
    xhr.vac_templater.aborted_by_same_category = false;

    // Cancel any running ajaxers with equal or less weight.
    // Weight 0 is reserved for non-abortable ajaxers that can safely
    // run concurrently with any other request.
    for (var i=0; i < ajaxers.length; i++) {
      if ((ajaxers[i].vac_templater.weight > 0) && (ajaxers[i].vac_templater.weight <= xhr.vac_templater.weight)) {
        if (xhr.vac_templater.category == ajaxers[i].vac_templater.category) {
          ajaxers[i].vac_templater.aborted_by_same_category = true;
        }
        ajaxers[i].abort();
      }
    }

    // Update ajaxers list.
    ajaxers.push(xhr);

    // Add ajaxing body class.
    $('body').addClass('ajaxing');

    // Add CSRF header (see https://docs.djangoproject.com/en/1.8/ref/csrf/#ajax).
    if (!safe_method(settings.type) && same_origin(settings.url)) {
      xhr.setRequestHeader("X-CSRFToken", vac_templater.csrf_token);
    }
  });

  $(document).ajaxComplete(function(event, xhr, settings) {
    // Update ajaxers list.
    for (var i=0; i < ajaxers.length; i++) {
      if (ajaxers[i].vac_templater.id === xhr.vac_templater.id) {
        ajaxers.splice(i, 1);
        break;
      }
    }

    // Remove ajaxing body class?
    if (ajaxers.length === 0) {
      $('body').removeClass('ajaxing');
    }
  });

})(jQuery);
