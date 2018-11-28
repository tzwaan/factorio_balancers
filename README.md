# factorio-balancers

## Description
This is a commandline program (and soon to be library) made to check
whether a factorio blueprint is a belt balancer.

It is able to check a multitude of things: Belt balance, belt throughput,
and a combination of both.

## Usage
The file you need to run is "balancer-test.py"

#### The following is the output of: 
> $ balancer-test.py -h

```
usage: balancer-test.py [-h] [-f FILE] [-nb] [-i NR_ITERATIONS] [-s] [-es]
                        [--string STRING]

Test a balancer configuration for its properties

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  The file from which to read the blueprint string
  -nb, --nobalance      If for any reason you don't want to test the balance
                        of the balancer
  -i NR\_ITERATIONS, --iterations NR\_ITERATIONS
                        The number of iterations you want the simulation to
                        run in each test. If not set, will use an estimation
                        based on the balancer design
  -s, --sweep           Performs a throughput test on all combinations where
                        exactly 1 or 2 inputs and outputs are used
  -es, --extensivesweep
                        Performs a throughput test on all combinations of the
                        same number of inputs and outputs
  --string STRING       The blueprint string to parse
```
