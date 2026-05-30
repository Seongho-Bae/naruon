cd scripts/ci
bash fast_test2.sh > out.txt 2>&1
cat out.txt | grep FAIL
