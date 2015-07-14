Add ons for Superlance, which is a package of plugins for Supervisord

Installation
==============

Use pip:
pip install git+git://github.com/sumitkumar1209/superlanceadds
<p>
Event listener meant to be subscribed to PROCESS_STATE_CHANGE events.  It will send mail when processes that are children of supervisord transition unexpectedly to the EXITED state and when they goto STARTING event from EXITED event supervisor config snippet that tells supervisor to use this script as a listener is below.</p>
<p><b>
[eventlistener:sesmail]<br>
command=/usr/local/bin/sesmailcli -o hostname -a -m notify-on-crash@domain.com -f crash-notifier@domain.com'<br>
events=PROCESS_STATE</b></p>
<p>or<br><b>
[eventlistener:sesmail]<br>
command=/usr/local/bin/sesmail<br>
events=PROCESS_STATE</b></p>

sesmailcmd.py [-p processname] [-e processname] [-a] [-o string] [-m emailto] [-f emailfrom]<br>or<br>sesmail.py<br>
The -p and -e option may be specified more than once, allowing for specification of multiple processes.  Specifying -a overrides any selection of -p.
A sample invocation:
crashmailcmd.py -p program1,group1:program2 -m dev@example.com<br>

config file is present in /etc/superlanceadds.conf
