#!/bin/bash

INSTANCE_DIR=${PREMISE_INSTANCE_DIR:-.}

INSTANCE=$INSTANCE_DIR/$1
shift
PARAMS=$@

PREDICT="premise-predict"
STATS="premise-mlstats"

echo "INSTANCE: $INSTANCE"
echo "PARAMS: $PARAMS"

$PREDICT $INSTANCE/used.syms $INSTANCE/train.deps $INSTANCE/used.seq -e $INSTANCE/eval.set $PARAMS | $STATS /dev/stdin $INSTANCE/eval.deps $INSTANCE/used.seq

