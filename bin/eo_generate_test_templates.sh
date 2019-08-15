#!/usr/bin/env bash

\rm -rf test_tmpl
mkdir test_tmpl
eo_specialize_code.py -l slot -t bias -n SlotTmplTest -s test -o test_tmpl/slot_tmpl_test.py
eo_specialize_code.py -l slot_table -t qe -n SlotTableTmplTest -s test -o test_tmpl/slot_table_tmpl_test.py
eo_specialize_code.py -l raft -t bias -n RaftTmplTest -s test -o test_tmpl/raft_tmpl_test.py
eo_specialize_code.py -l raft_table -t bias -n RaftTableTmplTest -s test -o test_tmpl/raft_table_tmpl_test.py
eo_specialize_code.py -l summary -t bias -n SummaryTmplTest -s test -o test_tmpl/summary_tmpl_test.py
