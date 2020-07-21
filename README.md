# factorio-balancers


## Description
This package provides a framework to import and test belt balancers
from the game factorio.

It is able to check a blueprint for belt input and output balance, full
throughput on regular use, and throughput unlimitedness.
It fully supports all vanilla belt types, sideloading and priority splitters
(currently ignores filters)

A website for balancers with this program integrated coming soon at
[factoriobalancers.com](http://factoriobalancers.com)


## Usage
You can use the ``balancer_test`` command to use the main balancer
testing tool on the command line.


#### The following is the output of:
> $ balancer_test -h

```
usage: balancer_test [-h] [-f FILE] [-nb] [-t] [-s] [-es] [--string STRING]
                     [--silent]

Test a balancer configuration for its properties

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  The file from which to read the blueprint string
  -nb, --nobalance      If for any reason you don't want to test the balance
                        of the balancer
  -t, --trickle         Performs a balance test using belts that are not full
  -s, --sweep           Performs a throughput test on all combinations where
                        exactly 1 or 2 inputs and outputs are used
  -es, --extensivesweep
                        Performs a throughput test on all combinations of the
                        same number of inputs and outputs
  --string STRING       The blueprint string to parse
  --silent              Tell the script not to write intermediate data to the
                        screen. Note: this prints raw function results on exit
                        that are very user-unfriendly.

```
