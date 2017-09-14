bsub_jupyter
------------

Connect to a LSF main node directly or trough a ssh jump node, launch a jupyter notebook via bsub and open automatically a tunnel. The name of the connection can be used to reestablish the connection later or to terminate it.



Installation
------------
```
git clone https://github.com/lucapinello/bsub_jupyter
cd bsub_jupyter
```

Add public key to the machine
-----------------------------
To avoid entering the password many many times to establish the connection those steps are necessary, BEFORE running the script.

Create a new ssh key if you don’t have one with the command

```
ssh-keygen
```
The key will be stored by default in: ~/.ssh/id_rsa.pub 

Install the utility ssh-copy-id if not available. 

On OSX this can be accomplished easily with the Homebrew packaging manager (https://brew.sh/). After installing homebrew type the command

```
brew install ssh-copy-id
```

While inside your network (or connected through the VPN) copy your public key to the main node machine with the command:

```
ssh-copy-id -i ~/.ssh/id_rsa.pub lp698@ssh.research.partners.org
```

If you are planning to use bsub_jupyter outside your VPN network copy also the public key to the bastion server:

```
ssh-copy-id -i ~/.ssh/id_rsa.pub lp698@eris1n2.research.partners.org
```

Finally, if you have not yet created a password for Jupyter on the remote machine, you need to do manually or using this nice utility:
https://github.com/paderijk/jupyter-password

Usage
-----
python bsub_jupyter username@server connection_name

For example:

```
python bsub_jupyter.py  lp698@eris1n2.research.partners.org my_connection2 --remote_path /data/pinello
```

You will see:

```
Checking if a connection alrady exists...
No running jobs were found, launching a new one!
JOB ID: 597500
Querying queue for job info.. . . .
Server launched on node: cn031
Local port: 9439  remote port: 9147
Should I open an ssh tunnel for you? [Y/n] y
Tunnel created! You can see your jupyter notebook server at: http://localhost:9439
Press Ctrl-c to interrupt the connection
```

Now you can open a browser and connect to the url provided, in this case http://localhost:9439 (the local and remote ports are generated at random between 9000 and 10000 to minimize conflicts with other users)

Once finished you can press Ctrl+c
```
Tunnel closed!
Should I kill also the job? [Y/n] n
```

If you didn't kill the job, you can reattach to it with the same command (since the connection name is the same!):

```
python bsub_jupyter.py  lp698@eris1n2.research.partners.org my_connection
```

```
A running job already exists!
JOB ID: 597500
Should I kill it? [Y/n] n
Querying queue for job info.. .
Server launched on node: cn031
Local port: 9439  remote port: 9147
Should I open an ssh tunnel for you? [Y/n] y
Tunnel created! You can see your jupyter notebook server at: http://localhost:9439
Press Ctrl-c to interrupt the connection
```

This time you see the option to also kill the job: Should I kill it? [Y/n] n

Or you can kill after you press Ctrl+c:
```
Tunnel closed!
Should I kill also the job? [Y/n] y
Job <597500> is being terminated
```

If you are in a network where the main node is behind a firewall and you can use an intermediate node you can use the option --bastion_server, for example:

```
python bsub_jupyter.py  lp698@eris1n2.research.partners.org my_connection --bastion_server lp698@ssh.research.partners.org
```

Other useful options are described in the command line help:

```
python bsub_jupyter.py --help
```

```
usage: bsub_jupyter.py [-h] [--bastion_server BASTION_SERVER]
                       [--memory MEMORY] [--n_cores N_CORES] [--queue QUEUE]
                       [--force_new_connection]
                       lsf_server connection_name

bsub_jupyter - Connect to a LSF main node directly or trough a ssh jump node,
launch a jupyter notebook via bsub and open automatically a tunnel.

positional arguments:
  lsf_server            username@server, the server is the main LSF node used
                        to submit jobs with bsub
  connection_name       Name of the connection

optional arguments:
  -h, --help            show this help message and exit
  --bastion_server BASTION_SERVER
                        SSH jump server, format username@server (default:
                        None)
  --memory MEMORY       Memory to request (default: 64000)
  --n_cores N_CORES     # of cores to request (default: 8)
  --queue QUEUE         Queue to submit job (default: big-multi)
  --force_new_connection
                        Ignore any existing connection file and start a new
                        connection (default: False)
```









