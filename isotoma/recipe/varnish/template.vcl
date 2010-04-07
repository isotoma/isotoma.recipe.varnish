# Copyright 2010 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# This is a basic VCL configuration file for varnish.  See the vcl(7)
# man page for details on VCL syntax and semantics.

#for $b in $backends
backend backend_$b['ID'] {
    .host = "$b['host']";
    .port = "$b['port']";
    .connect_timeout = $connect_timeout;
    .first_byte_timeout = $first_byte_timeout;
    .between_bytes_timeout = $between_bytes_timeout;
}
#end for

acl purge {
    "localhost";
    "127.0.0.1";
}

sub vcl_recv {
    set req.grace = 120s;

    if (req.request == "PURGE") {
        if (!client.ip ~ purge) {
            error 405 "Not allowed.";
        }
        lookup;
    }

    if (req.request != "GET" &&
        req.request != "HEAD" &&
        req.request != "PUT" &&
        req.request != "POST" &&
        req.request != "TRACE" &&
        req.request != "OPTIONS" &&
        req.request != "DELETE") {
        /* Non-RFC2616 or CONNECT which is weird. */
        pipe;
    }

    if (req.request != "GET" && req.request != "HEAD") {
        /* We only deal with GET and HEAD by default */
        pass;
    }

    if (req.http.If-None-Match) {
        pass;
    }

    if (req.url ~ "createObject") {
        pass;
    }

    remove req.http.Accept-Encoding;

    lookup;
}

sub vcl_pipe {
    # This is not necessary if you do not do any request rewriting.
    set req.http.connection = "close";
}

sub vcl_hit {
    if (req.request == "PURGE") {
        set obj.ttl = 0s;
        error 200 "Purged";
    }

    if (!obj.cacheable) {
        pass;
    }
}

sub vcl_miss {
    if (req.request == "PURGE") {
        error 404 "Not in cache";
    }

}

sub vcl_fetch {
    set obj.grace = 120s;
    if (obj.status = "302") {
        set obj.http.X-Cacheable = "NO:302";
        pass;
    }

    if (!obj.cacheable) {
        #if $verbose_headers
        set obj.http.X-Cacheable = "NO";
        #end if
        pass;
    }
    if (obj.http.Cache-Control ~ "(private|no-cache|no-store)") {
        #if $verbose_headers
        set obj.http.X-Cacheable = "NO:private";
        #end if
        pass;
    }
    #if $verbose_headers
    set obj.http.X-Cacheable = "YES";
    #end if
    deliver;
}

#if $verbose_headers
sub vcl_deliver {
        if (obj.hits > 0) {
                set resp.http.X-Cache = "HIT";
        } else {
                set resp.http.X-Cache = "MISS";
        }
}
#end if

