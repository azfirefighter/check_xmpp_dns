#!/usr/bin/env python

# Licensed as follows (this is the 2-clause BSD license, aka
# "Simplified BSD License" or "FreeBSD License"):
#
# Copyright (c) 2011-2014, Mark Doliner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# - Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# TODO: Maybe print a friendly warning if a DNS server returns a CNAME record
#       when we query for DNS SRV?  It's possible this is legit, and we should
#       recursively query the CNAME record for DNS SRV.  But surely not all
#       XMPP clients will do that.
# TODO: Add mild info/warning if client and server records point to different
#       hosts?  Or resolve to different hosts?  (aegee.org)
# TODO: Better info message if port is 443?  Talk about how clients might not
#       realize they need to use ssl?  (buddycloud.com)
# TODO: Better info message if port is 5223?  Talk about how clients might not
#       realize they need to use ssl?  (biscotti.com)
# TODO: Make sure record.target ends with a period?
# TODO: Add JavaScript to strip leading and trailing whitespace in the
#       hostname before submitting the form, so that the hostname is pretty in
#       the URL.

#import gevent.monkey; gevent.monkey.patch_all()

import cgi
import logging
import urllib

#import cgitb; cgitb.enable()
import dns.exception
import dns.resolver

# This is the main HTML template that makes up the page
MAIN_TEMPLATE = """<!DOCTYPE html>

<html>
<head>
<meta charset="utf-8">
<title>Check DNS SRV records for XMPP</title>

<style type="text/css">
.bluecontainer {
    background-color: #d0e0f8;
    border-radius: 10px;
    display: inline-block;
    padding: 0em 1em 0.5em 1em;
}

.footnote {
    color: #505050;
    font-size: 80%%;
    padding-left: 1.5em;
    text-indent: -1.5em;
}

.grey {
    color: #505050;
}

.red {
    color: #e00000;
}

.small {
    font-size: 80%%;
}

#formcontainer {
    background-color: #e0e0e0;
    border-radius: 10px;
    display: inline-block;
    padding: 1.5em;
}

#maincontent {
    background-color: #eeeeee;
    border-radius: 20px;
    padding: 1em 2em;
}

a:link {
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

a.hiddenlink:active, a.hiddenlink:link, a.hiddenlink:visited {
    color: #000000;
}

a.greyhiddenlink:active, a.greyhiddenlink:link, a.greyhiddenlink:visited {
    color: #505050;
}

body {
    background-color: #333333;
    font-family: sans-serif;
    padding: 2em;
}

h3 {
    margin-bottom: 0.5em;
}

hr {
    background-color: #000060;
    border: 0;
    height: 3px;
    margin: 2em auto 2em 0;
    width: 40%%;
}

p {
    max-width: 40em;
    margin-top: 0.5em;
}

table {
    border-collapse: collapse;
}

td, th {
    border: 1px dashed #c0c0c0;
    padding: 0.2em 0.5em;
    vertical-align: top;
}

td {
    font-family: monospace;
}
</style>

<script type="text/javascript">
/* Form validation */
function validate(field) {
    document.getElementById('submit_button').disabled = (field.value.length == 0);
}

/* Google Analytics */
(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');
ga('create', 'UA-514515-1', 'kingant.net');
ga('send', 'pageview');
</script>
</head>

<body>
<div id="maincontent">



<h1><a class="hiddenlink" href=".">Check DNS SRV records for XMPP</a></h1>

<div id="formcontainer">
<form action="?" method="GET">
<input id="input_box" name="h" onInput="validate(this)" value="%(hostname)s">
<input %(submit_button_disabled)sid="submit_button" type="submit" value="Check">
</form>
<div class="small grey" style="margin-left: 1em;">
ex: <a class="greyhiddenlink" href="?h=jabber.org">jabber.org</a><br>
ex: <a class="greyhiddenlink" href="?h=gmail.com">gmail.com</a><br>
ex: <a class="greyhiddenlink" href="?h=kingant.net">kingant.net</a>
</div>
</div>



%(body)s



<hr>
<h2>About</h2>
<p>The XMPP Core RFC describes a method of <a href="https://xmpp.org/rfcs/rfc6120.html#tcp-resolution-prefer">using DNS SRV records</a> to determine the host and port to connect to when logging into an XMPP account.  It can sometimes be tricky to configure these records.  Use this page as a tool to verify that your DNS SRV records are correct.</p>

<p>You can also fetch these records yourself with any of the following commands.<br>
<span class="small grey">Linux, OS X&gt;</span> <code>host -t SRV _xmpp-client._tcp.example.com</code><br>
<span class="small grey">Linux, OS X&gt;</span> <code>host -t SRV _xmpp-server._tcp.example.com</code><br>
<span class="small grey">Linux, OS X&gt;</span> <code>dig _xmpp-client._tcp.example.com SRV</code><br>
<span class="small grey">Linux, OS X&gt;</span> <code>dig _xmpp-server._tcp.example.com SRV</code><br>
<span class="small grey">Linux, OS X, Windows&gt;</span> <code>nslookup -querytype=SRV _xmpp-client._tcp.example.com</code><br>
<span class="small grey">Linux, OS X, Windows&gt;</span> <code>nslookup -querytype=SRV _xmpp-server._tcp.example.com</code>
</p>

<p><b>This Page</b><br>
Created by <a href="https://kingant.net/">Mark Doliner</a><br>
<a href="https://github.com/markdoliner/check_xmpp_dns">Source available</a> on GitHub
</p>

<p><b>Other Resources</b><br>
<a href="https://xmpp.net/">IM Observatory</a> (general info)<br>
<a href="http://www.process-one.net/en/imtrends/">IMtrends</a> (general info)<br>
<a href="https://www.olark.com/gtalk/check_srv">Olark's DNS SRV help page</a> (DNS SRV specific)<br>
<a href="https://support.google.com/a/answer/34143">Google's official help page for configuring server records</a> (DNS SRV specific)
</p>



</div>
</body>
</html>"""

TEMPLATE_ERROR = """<div style="margin: 1em 0em;" class="red">%s</div>"""

# These templates are used when there are no records for the given domain
TEMPLATE_NO_RECORDS = """<div style="margin: 1em 0em;"><div class="bluecontainer">
<h3>%s records for %%(hostname)s</h3>
%s
</div></div>"""
TEMPLATE_NO_RECORDS_CLIENT = TEMPLATE_NO_RECORDS % ('Client', '<p><span class="red">ERROR</span>: No xmpp-client DNS SRV records found!  XMPP clients will try to login to %(hostname)s on port 5222.  If this is incorrect then logging in will fail.</p>')
TEMPLATE_NO_RECORDS_SERVER = TEMPLATE_NO_RECORDS % ('Server', '<p><span class="red">ERROR</span>: No xmpp-server DNS SRV records found!  Other XMPP servers will try to peer with %(hostname)s on port 5269.  If this is incorrect then peering won\'t work correctly.</p>')

# These templates are used to display records for a given domain
TEMPLATE_RECORDS = """<div style="margin: 1em 0em;"><div class="bluecontainer">
<h3>%s records for %%(hostname)s</h3>
<p class="small">%s</p>
<table>
<tr><th>Target</th><th>Port</th><th>Priority</th><th>Weight</th></tr>
%%(rows)s
</table>
%%(footnotes)s
</div></div>"""
TEMPLATE_RECORDS_CLIENT = TEMPLATE_RECORDS % ('Client', 'XMPP clients will use these when logging in.')
TEMPLATE_RECORDS_SERVER = TEMPLATE_RECORDS % ('Server', 'Other XMPP servers will use these when peering with this domain.')

TEMPLATE_RECORD = """<tr>
<td>%(target)s</td>
<td>%(port)s</td>
<td>%(priority)s</td>
<td>%(weight)s</td>
%(errors)s
</tr>"""

def _sort_records(records):
    return sorted(records, key=lambda record: '%10d %10d %50s %d' % (record.priority, 1000000000 - record.weight, record.target, record.port))

def _get_records(records, peer_name, record_type, standard_port, conflicting_records):
    FLAG_NON_STANDARD_PORT = 1
    FLAG_CLIENT_SERVER_SHARED_PORT = 2
    footnotes_for_these_records = dict()

    # Create the list of result rows
    rows = []
    for record in records:
        notes_for_this_record = []
        if '%s:%s' % (record.target, record.port) in conflicting_records:
            notes_for_this_record.append((FLAG_CLIENT_SERVER_SHARED_PORT, '<span class="red">ERROR</span> This host+port is listed for both client and server records'))
        if record.port != standard_port:
            notes_for_this_record.append((FLAG_NON_STANDARD_PORT, 'INFO Non-standard port'))

        note_strings_for_this_record = []
        for (note_type, note_text) in notes_for_this_record:
            # Determine the flag number
            if note_type in footnotes_for_these_records:
                footnote_number = footnotes_for_these_records[note_type]
            else:
                footnote_number = len(footnotes_for_these_records) + 1
                footnotes_for_these_records[note_type] = footnote_number

            note_strings_for_this_record.append('%s<sup>%s</sup>' % (note_text, footnote_number))

        if len(note_strings_for_this_record):
            # The span in the following string shouldn't be necessary, but
            # Chrome was rendering the vertical alignment weirdly without it.
            errors = '<td><span>%s</span></td>' % '<br>'.join(note_strings_for_this_record)
        else:
            errors = ''

        rows.append(TEMPLATE_RECORD % dict(
            errors=errors,
            port=record.port,
            priority=record.priority,
            target=str(record.target).rstrip('.'), # Strip trailing period when displaying
            weight=record.weight,
        ))

    # Change the footnotes dictionary into a list sorted by value
    footnotes_for_these_records = sorted(footnotes_for_these_records.items(), key=lambda x: x[1])

    # Create the list of extended info about any problems we noticed
    footnotes = []
    for (flag_type, footnote_number) in footnotes_for_these_records:
        if flag_type == FLAG_CLIENT_SERVER_SHARED_PORT:
            footnotes.append('<p class="footnote">%s. XMPP clients and servers use different handshakes when connecting to servers, so it is not possible for a single hostname+port combination to accept traffic from clients and other servers (at least, I think that\'s true--please <a href="mailto:mark@kingant.net">correct me</a> if I\'m wrong!).</p>' % (footnote_number))
        elif flag_type == FLAG_NON_STANDARD_PORT:
            footnotes.append('<p class="footnote">%s. The customary port for %s connections is %s.  Using a different port isn\'t necessarily bad&mdash;%s that correctly use DNS SRV records will happily connect to this port&mdash;but we thought it was worth pointing out in case it was an accident.</p>' % (footnote_number, record_type, standard_port, peer_name))

    return ('\n'.join(rows), '\n'.join(footnotes))

def _get_authoritative_name_servers_for_domain(domain):
    """Return a list of strings containing IP addresses of the name servers
    that are considered to be authoritative for the given domain.

    This iteratively queries the name server responsible for each piece of the
    FQDN directly, so as to avoid any caching of results.
    """

    # Create a DNS resolver to use for these requests
    dns_resolver = dns.resolver.Resolver()

    # Set a 2.5 second timeout on the resolver
    dns_resolver.lifetime = 2.5

    # Iterate through the pieces of the hostname from broad to narrow. For
    # each piece, ask which name servers are authoritative for the next
    # narrower piece. Note that we don't bother doing this for the broadest
    # piece of the hostname (e.g. 'com' or 'net') because the list of root
    # servers should rarely change and changes shouldn't affect the outcome
    # of these queries.
    pieces = domain.split('.')
    for i in xrange(len(pieces)-1, 0, -1):
        broader_domain = '.'.join(pieces[i-1:])
        try:
            answer = dns_resolver.query(broader_domain, dns.rdatatype.NS)
        except dns.exception.SyntaxError:
            # TODO: Show "invalid hostname" for this?
            return
        except dns.resolver.NXDOMAIN:
            # TODO: Show an error message about this. "Unable to determine
            # authoritative name servers for domain X. These results might be
            # stale, up to the lifetime of the TTL."
            return
        except dns.resolver.NoAnswer:
            # TODO: Show an error message about this. "Unable to determine
            # authoritative name servers for domain X. These results might be
            # stale, up to the lifetime of the TTL."
            return
        except dns.resolver.NoNameservers:
            # TODO: Show an error message about this. "Unable to determine
            # authoritative name servers for domain X. These results might be
            # stale, up to the lifetime of the TTL."
            return
        except dns.resolver.Timeout:
            # TODO: Show an error message about this. "Unable to determine
            # authoritative name servers for domain X. These results might be
            # stale, up to the lifetime of the TTL."
            return

        new_nameservers = []
        for record in answer:
            if record.rdtype == dns.rdatatype.NS:
                # Got the hostname of a nameserver. Resolve it to an IP.
                # TODO: Don't do this if the nameserver we just queried gave us
                # an additional record that includes the IP.
                try:
                    answer2 = dns_resolver.query(record.to_text())
                except dns.exception.SyntaxError:
                    # TODO: Show "invalid hostname" for this?
                    return
                except dns.resolver.NXDOMAIN:
                    # TODO: Show an error message about this. "Unable to determine
                    # authoritative name servers for domain X. These results might be
                    # stale, up to the lifetime of the TTL."
                    return
                except dns.resolver.NoAnswer:
                    # TODO: Show an error message about this. "Unable to determine
                    # authoritative name servers for domain X. These results might be
                    # stale, up to the lifetime of the TTL."
                    return
                except dns.resolver.NoNameservers:
                    # TODO: Show an error message about this. "Unable to determine
                    # authoritative name servers for domain X. These results might be
                    # stale, up to the lifetime of the TTL."
                    return
                except dns.resolver.Timeout:
                    # TODO: Show an error message about this. "Unable to determine
                    # authoritative name servers for domain X. These results might be
                    # stale, up to the lifetime of the TTL."
                    return
                for record2 in answer2:
                    if record2.rdtype in (dns.rdatatype.A, dns.rdatatype.AAAA):
                        # Add the IP to the list of IPs.
                        new_nameservers.append(record2.address)
                    else:
                        # Unexpected record type
                        # TODO: Log something?
                        pass
            else:
                # Unexpected record type
                # TODO: Log something?
                pass

        dns_resolver.nameservers = new_nameservers

    return dns_resolver.nameservers

def _get_main_body(hostname):
    # Record domain name
    open('requestledger.txt', 'a').write('%s\n' % urllib.quote(hostname))

    # Sanity check hostname
    if hostname.find('..') != -1:
        return TEMPLATE_ERROR % 'Invalid hostname'

    # Create a DNS resolver to use for this request
    dns_resolver = dns.resolver.Resolver()

    # Set a 2.5 second timeout on the resolver
    dns_resolver.lifetime = 2.5

    # Look up the list of authoritative name servers for this domain and query
    # them directly when looking up XMPP SRV records. We do this to avoid any
    # potential caching from intermediate name servers.
    new_nameservers = _get_authoritative_name_servers_for_domain(hostname)
    if new_nameservers:
        dns_resolver.nameservers = new_nameservers
    else:
        # Couldn't determine authoritative name servers for domain.
        # TODO: Log something? Show message to user?
        pass

    # Lookup records
    try:
        client_records = dns_resolver.query('_xmpp-client._tcp.%s' % hostname, rdtype=dns.rdatatype.SRV)
    except dns.exception.SyntaxError:
        # TODO: Show "invalid hostname" for this
        client_records = []
    except dns.resolver.NXDOMAIN:
        client_records = []
    except dns.resolver.NoAnswer:
        # TODO: Show a specific message for this
        client_records = []
    except dns.resolver.NoNameservers:
        # TODO: Show a specific message for this
        client_records = []
    except dns.resolver.Timeout:
        # TODO: Show a specific message for this
        client_records = []
    client_records_by_endpoint = set('%s:%s' % (record.target, record.port) for record in client_records)

    try:
        server_records = dns_resolver.query('_xmpp-server._tcp.%s' % hostname, rdtype=dns.rdatatype.SRV)
    except dns.exception.SyntaxError:
        # TODO: Show "invalid hostname" for this
        server_records = []
    except dns.resolver.NXDOMAIN:
        server_records = []
    except dns.resolver.NoAnswer:
        # TODO: Show a specific message for this
        server_records = []
    except dns.resolver.NoNameservers:
        # TODO: Show a specific message for this
        server_records = []
    except dns.resolver.Timeout:
        # TODO: Show a specific message for this
        server_records = []
    server_records_by_endpoint = set('%s:%s' % (record.target, record.port) for record in server_records)

    # Construct output
    ret = []

    if client_records:
        client_records = _sort_records(client_records)
        (rows, footnotes) = _get_records(client_records, 'clients', 'client-to-server', 5222, server_records_by_endpoint)
        ret.append(TEMPLATE_RECORDS_CLIENT % dict(
            footnotes=footnotes,
            hostname=cgi.escape(hostname, True),
            rows=rows,
        ))
    else:
        ret.append(TEMPLATE_NO_RECORDS_CLIENT % dict(
            hostname=cgi.escape(hostname, True),
        ))

    ret.append('')

    if server_records:
        server_records = _sort_records(server_records)
        (rows, footnotes) = _get_records(server_records, 'servers', 'server-to-server', 5269, client_records_by_endpoint)
        ret.append(TEMPLATE_RECORDS_SERVER % dict(
            footnotes=footnotes,
            hostname=cgi.escape(hostname, True),
            rows=rows,
        ))
    else:
        ret.append(TEMPLATE_NO_RECORDS_SERVER % dict(
            hostname=cgi.escape(hostname, True),
        ))

    return '\n'.join(ret)

def _handle_request(env, start_response):
    form = cgi.FieldStorage(environ=env)

    if 'h' in form:
        hostname = form['h'].value.strip()
    else:
        hostname = ''

    if hostname:
        body = _get_main_body(hostname)
        submit_button_disabled = ''
    else:
        body = ''
        submit_button_disabled = 'disabled="disabled"'

    response_body = MAIN_TEMPLATE % dict(
        hostname=cgi.escape(hostname, True),
        body=body,
        submit_button_disabled=submit_button_disabled,
    )

    start_response('200 OK', [('Content-Type', 'text/html')])
    return [response_body]

def application(env, start_response):
    """WSGI application entry point."""

    try:
        return _handle_request(env, start_response)
    except:
        logging.exception('Unknown error handling request.  env=%s', env)
        raise

if __name__ == '__main__':
    logging.basicConfig(filename='log')

    import gevent.wsgi
    gevent.wsgi.WSGIServer(('', 1000), application=application).serve_forever()
