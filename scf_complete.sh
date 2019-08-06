#!/bin/bash
which scf > /dev/null 2>&1
if [ $? -ne 0 ]; then
    exit 1
fi
eval "$(_SCF_COMPLETE=source scf)" 
