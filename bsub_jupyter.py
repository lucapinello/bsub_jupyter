from __future__ import print_function
#!/usr/bin/env python
'''
Jupyter_Bsub - Luca Pinello & Kendell Clement 2017
Connect to a LSF main node directly or trough a ssh jump node, launch a jupyter notebook via bsub and open automatically a tunnel.
'''
__version__ = "0.3.0"


import subprocess as sb
import time
import re
import os
import sys
from random import randint
import argparse
import socket



def hostname_resolves(hostname):
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.error:
        return False


def query_yes_no(question, default="yes"):
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")

print('''
 _               _           _                   _
| |__  ___ _   _| |__       (_)_   _ _ __  _   _| |_ ___ _ __
| '_ \/ __| | | | '_ \      | | | | | '_ \| | | | __/ _ \ '__|
| |_) \__ \ |_| | |_) |     | | |_| | |_) | |_| | ||  __/ |
|_.__/|___/\__,_|_.__/____ _/ |\__,_| .__/ \__, |\__\___|_|
                    |_____|__/      |_|    |___/

''')
print('\n\n[Luca Pinello 2017, send bugs, suggestions or *green coffee* to lucapinello AT gmail DOT com]\n\n')
print( 'Version %s\n' % __version__)

parser = argparse.ArgumentParser(description='bsub_jupyter\n\n- Connect to a LSF main node directly or trough a ssh jump node, launch a jupyter notebook via bsub and open automatically a tunnel.',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('lsf_server', type=str,  help='username@server, the server is the main LSF node used to submit jobs with bsub')
parser.add_argument('connection_name', type=str,  help='Name of the connection')


#OPTIONALS
parser.add_argument('--remote_path', type=str,  help='remote path to use',default='~')
parser.add_argument('--bastion_server',  help='SSH jump server, format username@server', default=None)
parser.add_argument('--memory', type=int,  help='Memory to request', default=64000)
parser.add_argument('--n_cores', type=int,  help='# of cores to request', default=8)
parser.add_argument('--queue', type=str,  help='Queue to submit job',default='big-multi')
parser.add_argument('--force_new_connection',  help='Ignore any existing connection file and start a new connection', action='store_true')
parser.add_argument('--ignoreHostChecking',  help='Ignore known host checking. If your client-side tunnel is not created and you get a message starting "The authenticity of host {xxx} can\'t be established." try enabling this flag.', action='store_true')
parser.add_argument('--debug',  help='Print helpful debug messages', action='store_true')
parser.add_argument('--env', type=str, help='load a different env for python')

args = parser.parse_args()

username,hostname_server=args.lsf_server.split('@')


ssh_server=args.lsf_server
bastion_server=args.bastion_server

local_bastion_port=10001
ssh_port=22

if bastion_server:
    if not hostname_resolves(bastion_server):
        print('Cannot resolve bastion server %s. Check server name and try again.' % bastion_server)
        sys.exit(1)

    #ssh  -L 9000:eris1n2.research.partners.org:22 lp698@ssh.research.partners.org

    #create tunnel via bastion server
    cmd_bastion_tunnel='ssh -N -f -L {0}:{1}:{2} {3} '.format(local_bastion_port,hostname_server,ssh_port,bastion_server)
    if args.debug : print(cmd_bastion_tunnel)
    sb.call(cmd_bastion_tunnel,shell=True)

    ssh_server=" {0}@{1} -p {2} ".format(username,"localhost", local_bastion_port)

base_ssh_cmd="ssh"


if not hostname_resolves(hostname_server):
    print('Cannot resolve %s. Check server name and try again.' % hostname_server)
    sys.exit(1)


connection_name=args.connection_name
connection_filename='jupyter_connection_%s' % connection_name
queue=args.queue
memory=args.memory
n_cores=args.n_cores

random_local_port=randint(9000,10000)
random_remote_port=randint(9000,10000)

remote_path=args.remote_path

print('Checking if a connection alrady exists...')
#check if the connection  exists already
connection_status=sb.check_output('%s -t %s "[ -f %s ] && echo True|| echo False" 2> /dev/null' %(base_ssh_cmd,ssh_server, connection_filename),shell=True).strip()

if connection_status=='True' and not args.force_new_connection:

    print('A running job already exists!')

else:
	print('No running jobs were found, launching a new one! ')
	#launch a job
	if args.env:
		env_cmd=' source activate {0} && '.format(args.env)
	else:
		env_cmd=''

# TEST
	TIME='12:00'
#cmd_jupyter='%s -t %s "bsub  -q %s -n %d -M %d -cwd %s -R ' % (base_ssh_cmd,ssh_server,queue,n_cores,memory,remote_path) +"'rusage[mem=%d]'" % memory + " '"+env_cmd+" jupyter notebook --port=%d --no-browser '"%(random_remote_port)+' 2>&1 >%s "'%connection_filename+' 2>/dev/null'
	cmd_jupyter='%s -t %s "bsub -q %s -n %d -W %s -cwd %s -R ' % (base_ssh_cmd,ssh_server,queue,n_cores,TIME,remote_path) +"'rusage[mem=%d]'" % memory + "-N '"+env_cmd+"module load dev/python/2.7.6 ; jupyter notebook --port=%d --no-browser '"%(random_remote_port)+' 2>&1 >%s "'%connection_filename+' 2>/dev/null'
	if args.debug: print(cmd_jupyter)
	sb.call( cmd_jupyter,shell=True)
	cmd_file_write = '%s -t %s "echo %s,%s >> %s" 2> /dev/null' % (base_ssh_cmd,ssh_server,random_local_port, random_remote_port,connection_filename)
	if args.debug: print(cmd_file_write)
	sb.call(cmd_file_write,shell=True)
	connection_status=True

# TEST
job_id='_'.join(sb.check_output('%s %s " head -n 1 ~/%s" 2> /dev/null' % (base_ssh_cmd,ssh_server,connection_filename),shell=True).split(','))
random_local_port, random_remote_port=map(int,sb.check_output('%s %s "tail -n 1 ~/%s" 2> /dev/null' % (base_ssh_cmd,ssh_server,connection_filename),shell=True).strip().split(','))


print('JOB ID:',job_id)
job_id = job_id.split(' ')[1][1:-1]
print('NEW JOB ID:',job_id)

if connection_status=='True':
    if query_yes_no('Should I kill it?'):
        bkill_command='%s -t %s "bkill %s; rm %s" 2> /dev/null' % (base_ssh_cmd,ssh_server,job_id,connection_filename)
        sb.call(bkill_command,shell=True)
        sys.exit(0)

# use bjobs to get the node the server is running on
server = None
import time
time.sleep(10)
print('Querying queue for job info..')
while server is None:

    # TEST
    bjob_command='%s -t %s "bjobs -l %s"' % (base_ssh_cmd,ssh_server,job_id)
    if args.debug: print("bjob_command: " + bjob_command)
    p = sb.Popen(bjob_command, stdout=sb.PIPE, stderr=sb.PIPE,shell=True)
    out, err = p.communicate()
    sys.stdout.flush()

    #m = re.search('<(.*)>, Execution Home', out)
    m = re.search(r'<\d.*.orchestra', out)

    try:
        #server =  m.groups()[0].split('*')[-1]
        server = m.group(0).split('.')[0].split('*')[1]
    except AttributeError:
        time.sleep(1)

print('\nServer launched on node: '+server)

print('Local port: %d  remote port: %d' %(random_local_port, random_remote_port))

if sb.check_output("nc -z localhost %d || echo 'no tunnel open';" % random_local_port,shell=True).strip()=='no tunnel open':


    if query_yes_no('Should I open an ssh tunnel for you?'):

        sb.call('sleep 5 && python -m webbrowser -t "http://localhost:%d" & 2> /dev/null' % random_local_port,shell=True)

        tunnel_ssh_command = "ssh "
        if args.ignoreHostChecking: tunnel_ssh_command = "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "

#cmd_tunnel = tunnel_ssh_command + " -N  -L localhost:{0}:localhost:{1} -o 'ProxyCommand ssh {2} nc %h %p'  {3}@{4}.research.partners.org 2> /dev/null".format(random_local_port,random_remote_port,ssh_server,username,server)
        cmd_tunnel = tunnel_ssh_command + " -N  -L localhost:{0}:localhost:{1} -o 'ProxyCommand ssh {2} nc %h %p'  {3}@{4}.med.harvard.edu 2> /dev/null".format(random_local_port,random_remote_port,ssh_server,username,server)

        if args.debug: print(cmd_tunnel)

        try:

            print('Tunnel created! You can see your jupyter notebook server at:\n\n\t--> http://localhost:%d <--\n' % random_local_port)
            print('Press Ctrl-c to interrupt the connection')
            sb.call(cmd_tunnel,shell=True)
        except:
            print('Tunnel closed!')
            if query_yes_no('Should I kill also the job?'):
                bkill_command='%s -t %s "bkill %s; rm %s" 2> /dev/null' % (base_ssh_cmd,ssh_server,job_id,connection_filename)
                sb.call(bkill_command,shell=True)
                sys.exit(0)
else:
    print('Tunnel already exists!')
