import os
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.generic.climate import set_climate_constant

from simtools.SetupParser import SetupParser
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from malaria.interventions.malaria_challenge import add_challenge_trial
from malaria.reports.MalariaReport import add_patient_report
from simtools.ModBuilder import  ModFn, ModBuilder
from immunity_transitions_configuration import set_transition_matrix
# General
exp_name = 'Malariatherapy_2pt0_infections'
years = 1  # length of simulation, in years
immunity_forcing_on = 1

#Reading in from a config file specific for Malaria Functional Model which relies on 2.0 logic
##TODO Change to include user agnostic input folder address
config_path = r'C:\IDM\dtk-tools-malaria\examples\malariatherapy\input\from-cfg.json'

# Setup ----------------------------------------------------------------------------------------------------------
cb = DTKConfigBuilder.from_files(config_path)
cb.update_params({'Vector_Species_Names' : [],
                  'Simulation_Duration' : 365*years,
                  'Demographics_Filenames' : ['Malariatherapy_demographics.json']
                  })

set_climate_constant(cb)

# Specify immune parameters --------------------------------------------------------------------------------------
if immunity_forcing_on == 1:

    Transition_matrix = cb.config['parameters']['Parasite_Peak_Density_Probabilities']
    #What rows am I going to go about scaling? (Reminder... Row 0 transitions from truezero, and Row 6 is from highest density)
    immune_stim_threshold = 1
    #whats the base parameter I want to use to describe how immunity impacts these different density classes?
    #whats the base parameter I want to use to describe how immunity impacts the transitions within a density class?
    scale_factor_array = [2,5,10,100]

    builder = ModBuilder.from_combos(
        [ModFn(set_transition_matrix, Transition_matrix, scale_factor) for scale_factor in scale_factor_array]
    )
else:
    builder = ''

# Add source of infection (challenge bite or forced EIR) --------------------------------------------------------
add_challenge_trial(cb,start_day=0)

# ---- CUSTOM REPORTS ----
add_patient_report(cb)

# Run args
run_sim_args = {'config_builder': cb,
                'exp_name': exp_name,
                'exp_builder': builder
                }

if __name__ == "__main__":

    if not SetupParser.initialized:
        SetupParser.init('HPC')

    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    exp_manager.wait_for_finished(verbose=True)
    assert (exp_manager.succeeded())
