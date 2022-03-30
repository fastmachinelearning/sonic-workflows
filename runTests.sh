#!/bin/bash -ex

# fully loaded configuration: 3, 6, 18 threads
for NTH in 3 6 18; do
	./testCPU.sh -t testDirect_th${NTH} -n ${NTH} -j $((18/NTH))
	./testCPU.sh -t testSonic_th${NTH} -n ${NTH} -j $((18/NTH)) -s
done

# todo:
# test w/ single server for all jobs
# test w/ only ML modules in workflow? e.g. drop all other products & rely on unscheduled mode, would require higher duplicate factor
