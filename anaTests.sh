#!/bin/bash

for TEST in Direct Sonic SonicOne; do # SonicGPU SonicOneGPU; do
	for NTH in 1 3 6 18; do
		echo -e "${TEST}\t${NTH}\t$(grep -nr "Throughput" test${TEST}_th${NTH} | awk '{ sum += $(NF-1) } END { if (NR > 0) print sum / NR }')"
	done
done
