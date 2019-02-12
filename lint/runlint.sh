#!/bin/bash

flake8 --config=./lint/setup.cfg --show-source --statistics python
FLAKERC=$?
exit $FLAKERC

# Skip pylint for now
# pylint `find . -name \*.py -print`
# PYLINTRC=$?
# Fail Travis build if Pylint returns fatal (1) | error (2)
# if [ $(($PYLINTRC & 3)) -ne 0 ]; then
#    echo "Pylint failed"
#    exit 1
# else
#    echo "Pylint passed"
#    exit 0
#fi
