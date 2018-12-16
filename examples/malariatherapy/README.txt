This example was built as part of the work to improve the intrahost model of malaria by simulating and analyzing malariatherapy like infections using a scalable set of transition probabilities in a stochastic matrix. 

Built by Jon Russell (jorussell@idmod.org) in November 2018. 

Prereqs: Must have dtk-tools, dtk-tools-malaria packages installed. (run python setup.py or python setup.py develop for both pakcages).

Directory contents:

run_malariatherapy_dtk.py - runs 1-year simulations of malaria challenge bite infections.
immunity_transitions_configuration.py - contains helper functions for updating infection and immunity parameters (like first wave draw and transition probabilities)
analyze_infection_durations.py - example analyzer for looking at infection durations from challenge trial style infections from Malaria Patient Report 
bin/ - exe, dlls
input/ - Malariatherapy_demographics.json, from-cfg.json


Description:
Provides example uses of:
- building a config using .from_files command (run_malariatherapy_dtk)
- creating a Malaria Patient Report to monitor individual infections (run_malariatherapy_dtk)
- using ModFn to add sweeps across a particular scale factor (run_malariatherapy_dtk)
- Setting a constant climate (run_malariatherapy_dtk)
- adding a challenge trial intervention (run_malariatherapy_dtk)
- adding a tag (scale_factor) to each sim by returning (immunity_transitions_configuration)
- passing analyzers as a list (run_malariatherapy_dtk)


Note:

This run file uses the .from_files command for using a config file that details the necessary parameters for running this Malaria 2.0 logic.
cb = DTKConfigBuilder.from_files(config_path)

The immunity forcing block allows for the potential to scale the Transition Matrix values using pretty simple logic and relies on the ModFn tool to set up the scale_factor for each sim.
