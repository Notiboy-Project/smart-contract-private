#!/bin/bash

data=`./sandbox/sandbox goal app box info --name "b64:sbdFk0yRdX5fzZIs+UeRVElOiwZi1CaNCy4jBudgeBI=" --app-id 940 | tail -n1 | cut -d ':' -f3`
val=`echo "$data" | base64 -d`
echo $val
