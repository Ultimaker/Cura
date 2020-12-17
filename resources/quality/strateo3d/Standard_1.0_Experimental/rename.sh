#!/bin/sh

yourfilenames=`ls ./*.cfg`
for eachfile in $yourfilenames
do
    echo $eachfile
    echo >> $eachfile
    done
