#!/bin/bash

set -e

if [ ! -e "$1" ]; then
    echo "Usage: $0 <json_filename>"
    exit 1
fi

rm -f results.csv
echo "n,false_positive,false_negative,accuracy" >> /results.csv
for n in 20 40 60 80; do
    m=2
    false_positive_sum=0
    false_negative_sum=0
    accuracy_sum=0
    for i in `seq 1 $m`; do
        output=`python3 /tensorflow_learn.py $1 $n 2>/dev/null`
        output_arr=(${output//$'\n'/ })
        echo "n: $n false_positive: ${output_arr[0]} false_negative: ${output_arr[1]} accuracy: ${output_arr[2]}"
        false_positive_sum=$(echo "scale=2;$false_positive_sum + ${output_arr[0]}" | bc)
        false_negative_sum=$(echo "scale=2;$false_negative_sum + ${output_arr[1]}" | bc)
        accuracy_sum=$(echo "scale=2;$accuracy_sum + ${output_arr[2]}" | bc)
        NUMBER_MALICIOUS="${output_arr[3]}"
        NUMBER_BENIGN="${output_arr[4]}"
    done
    false_positive_avg=$(echo "scale=2;$false_positive_sum/$m" | bc)
    false_negative_avg=$(echo "scale=2;$false_negative_sum/$m" | bc)
    accuracy_avg=$(echo "scale=2;$accuracy_sum/$m" | bc)
    echo "$n,$false_positive_avg,$false_negative_avg,$accuracy_avg" >> /results.csv
done

python3 /plot_data.py


rm -f /RUN_INFO
grep "LEARNING_RATE" /config.ini >> /RUN_INFO
grep "NUM_CHUNKS" /config.ini >> /RUN_INFO
grep "SHUFFLE_CHUNKS" /config.ini >> /RUN_INFO
grep "DECAY_RATE" /config.ini >> /RUN_INFO
echo "NUMBER_MALICIOUS = $NUMBER_MALICIOUS" >> /RUN_INFO
echo "NUMBER_BENIGN = $NUMBER_BENIGN" >> /RUN_INFO
