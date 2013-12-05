#!/usr/bin/env python -u

# A event listener meant to be subscribed to PROCESS_STATE_CHANGE
# events.  It will send mail when processes that are children of
# supervisord transition unexpectedly to the EXITED state.

# A supervisor config snippet that tells supervisor to use this script
# as a listener is below.
#
# [eventlistener:sesmail]
# command=/usr/bin/sesmail -o hostname -a -m notify-on-crash@domain.com -f crash-notifier@domain.com'
# events=PROCESS_STATE
#
# Sendmail is used explicitly here so that we can specify the 'from' address.

doc = """\
sesmail.py [-p processname] [-a] [-o string] [-m emailto] [-f emailfrom]

The -p option may be specified more than once, allowing for
specification of multiple processes.  Specifying -a overrides any
selection of -p.

A sample invocation:

crashmail.py -p program1 -p group1:program2 -m dev@example.com

"""

import os
import sys

from supervisor import childutils

import boto.ses

def usage():
    print doc
    sys.exit(255)

class SesMail:

    def __init__(self, programs, any, emailto, emailfrom, optionalheader):

        self.programs = programs
        self.any = any
        self.emailto = emailto
        self.emailfrom = emailfrom
        self.optionalheader = optionalheader
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    def runforever(self, test=False):
        while 1:
            # we explicitly use self.stdin, self.stdout, and self.stderr
            # instead of sys.* so we can unit test this code
            headers, payload = childutils.listener.wait(self.stdin, self.stdout)

            if not headers['eventname'] == 'PROCESS_STATE_EXITED':
                # do nothing with non-TICK events
                childutils.listener.ok(self.stdout)
                if test:
                    self.stderr.write('non-exited event\n')
                    self.stderr.flush()
                    break
                continue

            pheaders, pdata = childutils.eventdata(payload+'\n')

            if int(pheaders['expected']):
                childutils.listener.ok(self.stdout)
                if test:
                    self.stderr.write('expected exit\n')
                    self.stderr.flush()
                    break
                continue

            msg = ('Process %(processname)s in group %(groupname)s exited '
                   'unexpectedly (pid %(pid)s) from state %(from_state)s' %
                   pheaders)

            subject = ' %s crashed at %s' % (pheaders['processname'],
                                             childutils.get_asctime())
            if self.optionalheader:
                subject = self.optionalheader + ':' + subject

            self.stderr.write('unexpected exit, mailing\n')
            self.stderr.flush()

            self.mail(subject, msg)

            childutils.listener.ok(self.stdout)
            if test:
                break

    def mail(self, subject, msg):
        conn = boto.ses.connect_to_region(self.region, aws_access_key_id=self.aws_id, aws_secret_access_key=self.aws_secret)
        resp = conn.send_email(self.from_email, subject, msg, [self.to_email])
        self.stderr.write('SES Response:\n%s\n' % resp)
        self.stderr.write('Mailed:\n\n%s\n' % msg)

def main(argv=sys.argv):
    import getopt
    short_args="hp:ao:m:f:r:"
    long_args=[
        "help",
        "program=",
        "any",
        "optionalheader="
        "emailto=",
        "emailfrom=",
        "region=",
        ]
    arguments = argv[1:]
    try:
        opts, args = getopt.getopt(arguments, short_args, long_args)
    except:
        usage()

    programs = []
    any = False
    emailto = None
    emailfrom = None
    optionalheader = None

    for option, value in opts:

        if option in ('-h', '--help'):
            usage()

        if option in ('-p', '--program'):
            programs.append(value)

        if option in ('-a', '--any'):
            any = True

        if option in ('-m', '--emailto'):
            emailto = value

        if option in ('-f', '--emailfrom'):
            emailfrom = value

        if option in ('-o', '--optionalheader'):
            optionalheader = value

    if not 'SUPERVISOR_SERVER_URL' in os.environ:
        sys.stderr.write('crashmail must be run as a supervisor event '
                         'listener\n')
        sys.stderr.flush()
        return

    prog = SesMail(programs, any, emailto, emailfrom, optionalheader)
    prog.runforever()

if __name__ == '__main__':
    main()


