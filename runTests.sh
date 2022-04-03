#!/bin/bash -ex

# fully loaded configuration: 3, 6, 18 threads
for NTH in 3 6 18; do
	./testCPU.sh -t testDirect_th${NTH} -n ${NTH} -j $((18/NTH))
	./testCPU.sh -t testSonic_th${NTH} -n ${NTH} -j $((18/NTH)) -s
	./testCPU.sh -t testSonicOne_th${NTH} -n ${NTH} -j $((18/NTH)) -s -m
# temporarily disabled for lack of memory
#	./testCPU.sh -t testSonicGPU_th${NTH} -n ${NTH} -j $((18/NTH)) -s -g
#	./testCPU.sh -t testSonicOneGPU_th${NTH} -n ${NTH} -j $((18/NTH)) -s -m -g
done

# todo:
# test w/ only ML modules in workflow? e.g. drop all other products & rely on unscheduled mode, would require higher duplicate factor
