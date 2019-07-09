#!/usr/bin/env bash

\rm -rf test_tmpl
mkdir test_tmpl
eo_specialize_code.py -l slot -t bias -n SlotTmplTest -s test -o test_tmpl/slot_tmpl_test.py
eo_specialize_code.py -l table -t bias -n TableTmplTest -s test -o test_tmpl/table_tmpl_test.py
eo_specialize_code.py -l raft -t bias -n RaftTmplTest -s test -o test_tmpl/raft_tmpl_test.py
eo_specialize_code.py -l summary -t bias -n SummaryTmplTest -s test -o test_tmpl/summary_tmpl_test.py
