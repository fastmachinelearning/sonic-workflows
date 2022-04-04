#!/bin/bash

for TEST in Direct Sonic SonicOne; do # SonicGPU SonicOneGPU; do
	for NTH in 1 3 6 18; do
		echo -e "${TEST}\t${NTH}\t$(grep -nr "Throughput" test${TEST}_th${NTH} | awk '{ sum += $(NF-1); sum2 += ($(NF-1))^2 } END { if (NR > 0) print sum / NR, sqrt((sum2 - sum^2/NR)/NR)/sqrt(NR) }')"
	done
done
