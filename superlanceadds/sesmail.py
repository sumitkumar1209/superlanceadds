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
import commands
import re

from supervisor import childutils

import boto.ses

def usage():
    print doc
    sys.exit(255)

class SesMail:
    """Provide email through SES when programs exit unexpectedly.
    """

    def __init__(self, programs=[], any=False, emailto=None, emailfrom=None, region=None, aws_id=None, 
            aws_secret=None, optionalheader=None):

        self.programs = programs
        self.any = any
        self.emailto = emailto
        self.emailfrom = emailfrom
        self.region = region
        self.aws_id = aws_id
        self.aws_secret = aws_secret
        self.optionalheader = optionalheader
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr

        code, stdoutbak = commands.getstatusoutput('ec2metadata')
        if code != 0:
            raise Exception('ec2metadata did not run correctly')
        mt = re.search('instance-id:\\s+(.*)', stdoutbak)
        if not mt:
            raise Exception('ec2metadata did not contain instance-id')
        self.instance_id = mt.groups(0)[0]

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

            pheaders['region'] = self.region
            pheaders['instance-id'] = self.instance_id

            msg = ('Process %(processname)s, in group %(groupname)s, '
                   'on instance %(instance-id)s, in region %(region)s exited '
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
        dakwargs = {}
        if self.aws_id:
            dakwargs['aws_access_key_id'] = self.aws_id
        if self.aws_secret:
            dakwargs['aws_secret_access_key'] = self.aws_secret
        conn = boto.ses.connect_to_region(self.region, **dakwargs)
        resp = conn.send_email(self.emailfrom, subject, msg, [self.emailto])
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
        "aws_id=",
        "aws_secret=",
        ]
    arguments = argv[1:]
    try:
        opts, args = getopt.getopt(arguments, short_args, long_args)
    except:
        usage()

    dakwargs = {}
    dakwargs['programs'] = []
    dakwargs['any'] = False

    for option, value in opts:

        if option in ('-h', '--help'):
            usage()

        if option in ('-p', '--program'):
            dakwargs['programs'].append(value)

        if option in ('-a', '--any'):
            dakwargs['any'] = True

        if option in ('-m', '--emailto'):
            dakwargs['emailto'] = value

        if option in ('-f', '--emailfrom'):
            dakwargs['emailfrom'] = value

        if option in ('-r', '--region'):
            dakwargs['region'] = value

        if option in ('-o', '--optionalheader'):
            dakwargs['optionalheader'] = value

        if option in ('--aws_id'):
            dakwargs['aws_id'] = value

        if option in ('--aws_secret'):
            dakwargs['aws_secret'] = value

    if not 'SUPERVISOR_SERVER_URL' in os.environ:
        sys.stderr.write('sesmail must be run as a supervisor event '
                         'listener\n')
        sys.stderr.flush()
        return

    prog = SesMail(**dakwargs)
    prog.runforever()

if __name__ == '__main__':
    main()


