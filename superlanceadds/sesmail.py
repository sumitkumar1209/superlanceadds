#!/usr/bin/env python -u

# A event listener meant to be subscribed to PROCESS_STATE_CHANGE
# events.  It will send mail when processes that are children of
# supervisord transition unexpectedly to the EXITED state and when they goto
# STARTING event from EXITED event
# A supervisor config snippet that tells supervisor to use this script
# as a listener is below.
#
# [eventlistener:sesmail]
# command=/usr/local/bin/sesmail
# events=PROCESS_STATE

doc = """\
A sample invocation:
sesmail.py

"""

import os
import sys
import ConfigParser
from supervisor import childutils
import boto.ses


def usage():
    print doc
    sys.exit(255)


class SesMail:
    """Provide email through SES when programs exit unexpectedly.
    """

    def __init__(self, programs=None, excluded=None, any=False, emailto=None, emailfrom=None, aws_id=None,
                 aws_secret=None, optionalheader=None):

        if not excluded:
            excluded = []
        if not programs:
            programs = []
        self.programs = programs
        self.excluded = excluded
        self.any = any
        self.emailto = emailto
        self.emailfrom = emailfrom
        self.aws_id = aws_id
        self.aws_secret = aws_secret
        self.optionalheader = optionalheader
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    def runforever(self):
        while 1:
            # we explicitly use self.stdin, self.stdout, and self.stderr
            # instead of sys.* so we can unit test this code
            headers, payload = childutils.listener.wait(self.stdin, self.stdout)
            pheaders, pdata = childutils.eventdata(payload + '\n')
            pheaders['eventname'] = headers['eventname'].split('_')[-1]
            self.stderr.write(str(self.excluded))
            if not headers['eventname'] == 'PROCESS_STATE_EXITED' and not pheaders['from_state'] == 'EXITED' and not \
                    headers['eventname'] == 'PROCESS_STATE_FATAL':
                # do nothing with non-TICK events
                childutils.listener.ok(self.stdout)
                continue
            if pheaders['processname'] in self.excluded:
                # do nothing with excluded processes
                childutils.listener.ok(self.stdout)
                continue
            if not self.any and pheaders['processname'] not in self.programs:
                # do nothing with processes not asked
                childutils.listener.ok(self.stdout)
                continue
            msg = ('Process %(processname)s, in group %(groupname)s, '
                   ' moved to %(eventname)s from state %(from_state)s' %
                   pheaders)

            subject = ' %s %s at %s' % (pheaders['processname'], pheaders['eventname'],
                                        childutils.get_asctime())
            if self.optionalheader:
                subject = self.optionalheader + ':' + subject

            self.mail(subject, msg)

            childutils.listener.ok(self.stdout)

    def mail(self, subject, msg):
        dakwargs = {}
        if self.aws_id:
            dakwargs['aws_access_key_id'] = self.aws_id
        if self.aws_secret:
            dakwargs['aws_secret_access_key'] = self.aws_secret
        conn = boto.ses.SESConnection(**dakwargs)
        resp = conn.send_email(self.emailfrom, subject, msg, [self.emailto])
        self.stderr.write('SES Response:\n%s\n' % resp)
        self.stderr.write('Mailed:\n\n%s\n' % msg)

def main():
    config = ConfigParser.ConfigParser()
    config.read("/etc/superlanceadds.conf")
    dakwargs = dict(programs=config.get("Processes", 'Include').split(','),
                    excluded=config.get("Processes", "Exclude").split(','),
                    any=bool(config.get("Processes", "All")), aws_id=config.get("Credentials", "AwsId"),
                    aws_secret=config.get("Credentials", "AwsSecret"), emailfrom=config.get("Email", "From"),
                    emailto=config.get("Email", "To").split(','))

    if 'SUPERVISOR_SERVER_URL' not in os.environ:
        sys.stderr.write('sesmail must be run as a supervisor event '
                         'listener\n')
        sys.stderr.flush()
        return

    prog = SesMail(**dakwargs)
    prog.runforever()


if __name__ == '__main__':
    main()
