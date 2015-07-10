Add ons for Superlance, which is a package of plugins for Supervisord

Installation
==============

Use pip:

pip install git+git://github.com/sumitkumar1209/superlanceadds

Event listener meant to be subscribed to PROCESS_STATE_CHANGE events.  It will send mail when processes that are children of supervisord transition unexpectedly to the EXITED state and when they goto STARTING event from EXITED event supervisor config snippet that tells supervisor to use this script as a listener is below.
<b>
[eventlistener:sesmail]
command=/usr/local/bin/sesmail -o hostname -a -m notify-on-crash@domain.com -f crash-notifier@domain.com'
events=PROCESS_STATE</b>


sesmail.py [-p processname] [-e processname] [-a] [-o string] [-m emailto] [-f emailfrom]
The -p and -e option may be specified more than once, allowing for specification of multiple processes.  Specifying -a overrides any selection of -p.

A sample invocation:

crashmail.py -p program1,group1:program2 -m dev@example.com
