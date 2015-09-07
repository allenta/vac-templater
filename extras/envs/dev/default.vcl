vcl 4.0;

/*
 * # VAC Templater meta definitions. Settings here defined may be used through all
 * # the VCL code (even multiple times) and the VAC Templater utility will be able
 * # to provide a graphic interface to easily modify its values and deploy
 * # these changes to production by communicating with the VAC.
 * vac-templater:
 *   # Users with special roles.
 *   # VAC Templater uses the VAC to identify users so there's no need to list all
 *   # of them here. Only users with special roles should be listed so that
 *   # write permissions on individual settings can be later restricted to those
 *   # roles. All users have the implicit role 'user', that needn't be included
 *   # in these lists.
 *   users:
 *     - vac: ['admin', 'developer']
 *     - alice: ['admin']
 *     - bob: ['developer']
 *
 *   # Settings. All settings have a name, a type, an optional description and
 *   # an optional list of validators.
 *   #
 *   # Type may be one of 'text', 'longtext', 'integer', 'duration', 'boolean'
 *   # 'acl', 'select' or 'group' and each one accepts different kinds of
 *   # validators.
 *   #
 *   # Settings can also be restricted to a particular role (only users with
 *   # that particular role will be able to modify that setting). All settings
 *   # are restricted to the implicit role 'user' by default.
 *   settings:
 *     # 'Boolean' settings accept no validator. There are three ways of
 *     # representing a boolean: as a true boolean in VCL (bool, default), as a
 *     # string (str, '0' | '1') or as an integer (int, 0 | 1). Check how this
 *     # setting is used in the VCL below to see how a boolean can be
 *     # represented as a string in VCL. The same setting may be used multiple
 *     # times in VCL and be represented each time differently, that's why the
 *     # representation is not part of the setting definition.
 *     - debug:
 *         name: Debug
 *         description: >
 *             Enable debugging to receive handy response headers and collect
 *             useful information in varnishlog.
 *         type: boolean
 *
 *     # 'acl' settings accept no validator.
 *     - purge-acl:
 *         name: Purge ACL
 *         description: ACL to restrict the ability to purge cached contents.
 *         type: acl
 *         role: admin
 *
 *     # 'integer' settings accept the following validators: min and max.
 *     # There are also two ways of representing an integer: as a true
 *     # integer in VCL (int, default), or as a string (str).
 *     - max-retries:
 *         name: Max retries
 *         description: >
 *              Maximum number of times a request is to be retried when the
 *              backend is behaving unexpectedly.
 *         type: integer
 *         role: admin
 *         validators:
 *           min: 0
 *           max: 5
 *
 *     # Settings may be grouped together in a group, which is just another
 *     # setting with the type 'group'. Concrete settings come under the
 *     # 'settings' key.
 *     # Groups can also be restricted to a specific role, which will affect
 *     # all its child settings unless overridden.
 *     - backend:
 *         name: Backend
 *         description: Default backend definition
 *         type: group
 *         role: admin
 *         settings:
 *           # 'text' settings accept the following validators: min, max (both
 *           # refering to the text size) and regexp (a regular expression that
 *           # the text has to match).
 *           - host:
 *               name: Host
 *               description: Default backend's IP.
 *               type: text
 *               validators:
 *                 regexp: ^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$
 *
 *           - port:
 *               name: Port
 *               type: integer
 *               validators:
 *                 min: 0
 *                 max: 65535
 *
 *     - modes:
 *         name: Modes
 *         type: group
 *         role: admin
 *         settings:
 *           # 'select' settings only accept a single validator: options, which
 *           # lists the available values for the setting.
 *           - mode:
 *               name: Mode
 *               type: select
 *               validators:
 *                 options:
 *                   - normal
 *                   - cache-all
 *                   - maintenance
 *
 *           # 'duration' settings accept the following validators: min and max.
 *           - cache-all-ttl:
 *               name: Cache-all mode TTL
 *               description: >
 *                   All contents will be cached with the selected TTL while in
 *                   cache-all mode.
 *               type: duration
 *               validators:
 *                 min: 0s
 *                 max: 5m
 *
 *           # 'longtext' settings accept the following validators: min, max
 *           # (both refering to the text size) and regexp (a regular expression
 *           # that the text has to match).
 *           - maintenance-html:
 *               name: Maintenance mode HTML
 *               description: >
 *                   Static HTML that will be served to clients while in
 *                   maintenance mode.
 *               type: longtext
 *               role: developer
 *               validators:
 *                 min: 1
 */

import std;
import var;

acl purge {
    /* {{ purge-acl */
    "localhost";
    /* }} */
}

backend default {
    .host = /* {{ backend:host */"127.0.0.1"/* }} */;
    .port = /* {{ backend:port|str */"80"/* }} */;
}

sub vcl_init {
    # Set mode.
    var.global_set("mode", /* {{ modes:mode */"normal"/* }} */);

    # Enable/disable debugging.
    var.global_set("debug", /* {{ debug|str */"0"/* }} */);
}

sub vcl_recv {
    # Maintenance mode?
    if (var.global_get("mode") == "maintenance") {
        return (synth(700, "Maintenance mode"));
    }

    # Purge.
    if (req.method == "PURGE") {
        if (!client.ip ~ purge) {
            return (synth(405, "Not allowed"));
        }
        return (purge);
    }
}

sub vcl_deliver {
    # Debug enabled?
    if (var.global_get("debug") == "1") {
        if (obj.hits > 0) {
            set resp.http.X-Cache = "HIT";
        } else {
            set resp.http.X-Cache = "MISS";
        }
    }
}

sub vcl_synth {
    if (resp.status == 700) {
        set resp.status = 200;
        set resp.reason = "OK";

        set resp.http.Content-Type = "text/html; charset=utf-8";
        set resp.http.Cache-Control = "no-cache, no-store, must-revalidate";
        set resp.http.Pragma = "no-cache";
        set resp.http.Expires = "0";

        synthetic(/* {{ modes:maintenance-html */{"<!DOCTYPE html>
<html>
  <head>
    <title>Maintenance mode</title>
  </head>
  <body>
    <h1>Sorry, but we are on maintenance mode</h1>
    <p>We'll be back as soon as possible!</p>
  </body>
</html>"}/* }} */);

        return (deliver);
    }
}

sub vcl_backend_fetch {
    if (bereq.retries == 0) {
        # Clean up the X-Varnish-Backend-5xx flag that is used internally
        # to mark broken backend responses that should be retried.
        unset bereq.http.X-Varnish-Backend-5xx;
    } else {
        if (bereq.http.X-Varnish-Backend-5xx) {
            if (bereq.method != "POST" &&
                std.healthy(bereq.backend) &&
                bereq.retries <= /* {{ max-retries */4/* }} */) {
                # Flush broken backend response flag & try again.
                unset bereq.http.X-Varnish-Backend-5xx;
                if (var.global_get("debug") == "1") {
                    std.log(
                        "Retrying request. Retries: " +
                        bereq.retries + "/" +
                        /* {{ max-retries|str */"4"/* }} */);
                }
            } else {
                return (abandon);
            }
        }
    }
}

sub vcl_backend_response {
    # Retry broken backend responses.
    if (beresp.status >= 500 && beresp.status < 600) {
        set bereq.http.X-Varnish-Backend-5xx = "1";
        return (retry);
    }

    # Cache-all mode?
    if (var.global_get("mode") == "cache-all") {
        # Cache everything ignoring any cache headers.
        set beresp.ttl = /* {{ modes:cache-all-ttl */5m/* }} */;
    }
}

sub vcl_backend_error {
    # Retry broken backend responses.
    set bereq.http.X-Varnish-Backend-5xx = "1";
    return (retry);
}
