(function ($) {

  vac_templater.partials = vac_templater.partials || { registry: {} };

  /**
   *
   */
  vac_templater.partials.ready = function(id, options) {
    if (id in vac_templater.partials.registry) {
      var partial = vac_templater.partials.registry[id](options);
      vac_templater.ready(partial.callback, partial.ready, partial.unloader);
    }
  };

})(jQuery);

/******************************************************************************
 * VCL > Deploy.
 ******************************************************************************/

(function ($) {
  vac_templater.partials.registry['vcl-deploy-page'] = function(options) {
    return {
      callback: function(context) {
        // Make sure pressing the "enter" key in any of the settings fields
        // (except selects, or textareas) submits the form as if the "deploy"
        // button was pressed (and not the group selection button of the first
        // step).
        $('#modify-settings input', context).keypress(function(event) {
          if (event.which == 13) {
            event.preventDefault();
            event.stopPropagation();
            $('button[value="deploy"]', context).click();
          }
        });

        // Transform strftm format used in Django to the format used by Moment.js
        // (and therefore, by Bootstrap Datetimepicker).
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

        var format = options.datetime_format.replace(
          new RegExp(Object.keys(replacements).map(function(val) {
            return '%' + val; }).join('|'), 'g'),
          function myFunction(val) {
            return replacements[val.substring(1)];
          });

        // Transform time inputs into a Datetimepicker-enhanced input.
        $('.form-group.time input').datetimepicker({
          format: format
        });
      }
    };
  };
})(jQuery);

/******************************************************************************
 * VCL > History.
 ******************************************************************************/

(function ($) {
  vac_templater.partials.registry['vcl-history-page'] = function(options) {
    return {
      callback: function(context) {
        (function (browser) {
          function get_filters(overrides) {
            var filters = {};
            $('.collection-filter form :input:not("button")', browser).each(function() {
              if ($(this).val()) {
                filters[$(this).attr('name')] = $(this).val();
              }
            });
            return $.extend(filters, overrides || {});
          }

          function get_settings(overrides) {
            return $.extend({
              items_per_page: $('.collection-items-per-page li.active', browser).attr('data-collection-items-per-page'),
              sort_criteria: $('.collection-sort li.active', browser).attr('data-sort-criteria'),
              sort_direction: $('.collection-sort li.active', browser).attr('data-sort-direction')
            }, overrides || {});
          }

          function build_url(page, filters, settings) {
            params = $.extend({'page': page}, filters, settings);
            return options.browse_url + '?' + $.param(params);
          }

          $('.collection-filter form', browser).submit(function() {
            window.location.href = build_url(1, get_filters(), get_settings());
            return false;
          });

          $('.collection-sort li', browser).click(function() {
            var new_settings = {};
            if ($(this).hasClass('active')) {
              new_settings.sort_direction = ($(this).attr('data-sort-direction') == 'asc') ? 'desc' : 'asc';
            } else {
              new_settings.sort_criteria = $(this).attr('data-sort-criteria');
            }
            window.location.href = build_url(1, get_filters(), get_settings(new_settings));
            return false;
          });

          $('.collection-items-per-page li', browser).click(function() {
            window.location.href = build_url(1, get_filters(), get_settings({
              items_per_page: $(this).attr('data-collection-items-per-page')
            }));
            return false;
          });

          $('.collection-pager li:not(.disabled)', browser).click(function() {
            window.location.href = build_url($(this).attr('data-page'), get_filters(), get_settings());
            return false;
          });

          $('.deployments a.filter', browser).click(function() {
            var filters = {};
            filters[$(this).attr('data-field')] = $(this).attr('data-value');
            $(this).attr('href', build_url(1, filters, get_settings()));
          });
        })($(context).find('.deployments-browser'));
      }
    };
  };
})(jQuery);
