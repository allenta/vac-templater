(function ($) {
  /******************************************************************************
   * CLIENT.
   ******************************************************************************/

  /**
   * Portions of this code from Professional JavaScript for Web Developers, ISBN: 978-0-470-22780-0,
   * copyright John Wiley & Sons, Inc.: 2009, by Nicholas C. Zakas,
   * published under the Wrox imprint are used by permission of John Wiley & Sons, Inc All rights reserved.
   * This book and the Wrox code are available for purchase or download at www.wrox.com"   * [client description]
   */
  vac_templater.client = function() {
    // Rendering engines.
    var engine = {
      ie: 0,
      gecko: 0,
      webkit: 0,
      khtml: 0,
      opera: 0,
      // Complete version.
      ver: null
    };

    // Browsers.
    var browser = {
      // Browsers.
      ie: 0,
      firefox: 0,
      safari: 0,
      konq: 0,
      opera: 0,
      chrome: 0,
      // Specific version.
      ver: null
    };

    // Platform/device/OS.
    var system = {
      win: false,
      mac: false,
      x11: false,
      // Mobile devices.
      iphone: false,
      ipod: false,
      nokiaN: false,
      winMobile: false,
      macMobile: false,
      // Game systems.
      wii: false,
      ps: false
    };

    // Detect rendering engines/browsers.
    var ua = navigator.userAgent;
    if (window.opera) {
      engine.ver = browser.ver = window.opera.version();
      engine.opera = browser.opera = parseFloat(engine.ver);
    } else if (/AppleWebKit\/(\S+)/.test(ua)) {
      engine.ver = RegExp["$1"];
      engine.webkit = parseFloat(engine.ver);
      // Figure out if it's Chrome or Safari.
      if (/Chrome\/(\S+)/.test(ua)) {
        browser.ver = RegExp["$1"];
        browser.chrome = parseFloat(browser.ver);
      } else if (/Version\/(\S+)/.test(ua)) {
        browser.ver = RegExp["$1"];
        browser.safari = parseFloat(browser.ver);
      } else {
        // Approximate version.
        var safariVersion = 1;
        if (engine.webkit < 100) {
            safariVersion = 1;
        } else if (engine.webkit < 312) {
            safariVersion = 1.2;
        } else if (engine.webkit < 412) {
            safariVersion = 1.3;
        } else {
            safariVersion = 2;
        }
        browser.safari = browser.ver = safariVersion;
      }
    } else if (/KHTML\/(\S+)/.test(ua) || /Konqueror\/([^;]+)/.test(ua)) {
      engine.ver = browser.ver = RegExp["$1"];
      engine.khtml = browser.konq = parseFloat(engine.ver);
    } else if (/rv:([^\)]+)\) Gecko\/\d{8}/.test(ua)) {
      engine.ver = RegExp["$1"];
      engine.gecko = parseFloat(engine.ver);
      // Determine if it's Firefox.
      if (/Firefox\/(\S+)/.test(ua)) {
          browser.ver = RegExp["$1"];
          browser.firefox = parseFloat(browser.ver);
      }
    } else if (/MSIE ([^;]+)/.test(ua)) {
      engine.ver = browser.ver = RegExp["$1"];
      engine.ie = browser.ie = parseFloat(engine.ver);
    }

    // Detect browsers.
    browser.ie = engine.ie;
    browser.opera = engine.opera;

    // Detect platform.
    var p = navigator.platform;
    system.win = p.indexOf("Win") === 0;
    system.mac = p.indexOf("Mac") === 0;
    system.x11 = (p == "X11") || (p.indexOf("Linux") === 0);

    // Detect windows operating systems.
    if (system.win) {
      if (/Win(?:dows )?([^do]{2})\s?(\d+\.\d+)?/.test(ua)) {
        if (RegExp["$1"] == "NT") {
          switch(RegExp["$2"]) {
            case "5.0":
              system.win = "2000";
              break;
            case "5.1":
              system.win = "XP";
              break;
            case "6.0":
              system.win = "Vista";
              break;
            default:
              system.win = "NT";
              break;
          }
        } else if (RegExp["$1"] == "9x") {
          system.win = "ME";
        } else {
          system.win = RegExp["$1"];
        }
      }
    }

    // Mobile devices.
    system.iphone = ua.indexOf("iPhone") > -1;
    system.ipad = ua.indexOf("iPad") > -1;
    system.ipod = ua.indexOf("iPod") > -1;
    system.nokiaN = ua.indexOf("NokiaN") > -1;
    system.winMobile = (system.win == "CE");
    system.macMobile = (system.iphone || system.ipod);

    // Gaming systems.
    system.wii = ua.indexOf("Wii") > -1;
    system.ps = /playstation/i.test(ua);

    // Done!
    return {
      engine: engine,
      browser: browser,
      system: system
    };
  }();

  vac_templater.is_outdated_browser = function() {
    return (
      (vac_templater.client.browser.ie >= 1 && vac_templater.client.browser.ie <= 8) ||
      (vac_templater.client.browser.firefox >= 1 && vac_templater.client.browser.firefox <= 10) ||
      (vac_templater.client.browser.safari >= 1 && vac_templater.client.browser.safari <= 5) ||
      (vac_templater.client.browser.opera >= 1 && vac_templater.client.browser.opera <= 10) ||
      (vac_templater.client.browser.chrome >= 1 && vac_templater.client.browser.chrome <= 10)
    );
  };

  /******************************************************************************
   * DEVELOPMENT.
   ******************************************************************************/

  /**
   *
   */
  vac_templater.dev = {
    logging: false,

    log: function(message) {
      if (vac_templater.dev.logging && (typeof(console) != 'undefined')) {
        console.log(message);
      }
    }
  };

  /******************************************************************************
   * CHECK BROWSER & COMPLETE JS LOADING.
   ******************************************************************************/

  if (!vac_templater.is_outdated_browser()) {
    // Complete JS loading.
    var urls = media_urls('default-bundle.js?language=' + vac_templater.language);
    for(var i = 0; i < urls.length; i++) {
      $.ajax({
        url: urls[i],
        dataType: 'script',
        cache: true,
        async: false
      });
    }
  } else {
    // Add dummy versions of some methods used in templates.
    vac_templater.ready = function() { };
    vac_templater.partials = { ready: function() { }};

    // Show modal suggesting browser upgrade.
    $(document).ready(function() {
      var modal = $(
        '<div class="modal fade">' +
        '  <div class="modal-dialog">' +
        '    <div class="modal-content">' +
        '      <div class="modal-header">' +
        '        <h3>' + gettext('Upgrade your browser') + '</h3>' +
        '      </div>' +
        '      <div class="modal-body container-fluid">' +
        '        <p>' + gettext('Your browser is outdated! Please, download an updated version now and improve your user experience.') + '</p>' +
        '        <div class="row">' +
        '          <div class="col-xs-3"><a href="http://www.google.com/chrome/"><img alt="Chrome" title="Chrome" class="col-xs-10 col-xs-offset1" src="' + media_url('vac-templater/default/images/browsers/chrome.png') + '"/></a></div>' +
        '          <div class="col-xs-3"><a href="http://www.mozilla.org/firefox/"><img alt="Firefox" title="Firefox" class="col-xs-10 col-xs-offset1" src="' + media_url('vac-templater/default/images/browsers/firefox.png') + '"/></a></div>' +
        '          <div class="col-xs-3"><a href="http://www.opera.com"><img alt="Opera" title="Opera" class="col-xs-10 col-xs-offset1" src="' + media_url('vac-templater/default/images/browsers/opera.png') + '"/></a></div>' +
        '          <div class="col-xs-3"><a href="http://www.apple.com/safari/"><img alt="Safari" title="Safari" class="col-xs-10 col-xs-offset1" src="' + media_url('vac-templater/default/images/browsers/safari.png') + '"/></a></div>' +
        '        </div>' +
        '      </div>' +
        '      <div class="modal-footer">' +
        '        <a href="http://www.updatebrowser.net" class="btn btn-primary"><i class="glyphicon glyphicon-download-alt glyphicon-white"></i> ' + gettext('Choose your new browser') + '</a>' +
        '      </div>' +
        '    </div>' +
        '  </div>' +
        '</div>');
      $('#overlay').append(modal);
      modal.modal({
        show: true,
        backdrop: 'static',
        keyboard: false
      });
    });
  }
})(jQuery);
