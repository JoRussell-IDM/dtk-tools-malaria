import os

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.generic.climate import set_climate_constant

from simtools.SetupParser import SetupParser
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from malaria.interventions.malaria_challenge import add_challenge_trial

from dtk.interventions.input_EIR import add_InputEIR
from malaria.reports.MalariaReport import add_patient_report

# General
exp_name = '2pt0_infections'
years = 1  # length of simulation, in years

#Reading in from a config file specific for Malaria Functional Model which relies on 2.0 logic

config_path = os.path.join(os.path.expanduser('~'), 'Dropbox (IDM)',
                              'Malaria Team Folder', 'projects',
                              'updated_infection_and_immunity', 'malaria-two-pt-oh','bin','from-cfg.json')

# Setup ----------------------------------------------------------------------------------------------------------
cb = DTKConfigBuilder.from_files(config_path)
cb.update_params({'Vector_Species_Names' : [],
                  'Simulation_Duration' : 365*years,
                  'Demographics_Filenames' : ['Malariatherapy_demographics.json']
                  })

set_climate_constant(cb)

# Specify immune parameters --------------------------------------------------------------------------------------
use_manual_scaling = 1

Transition_matrix = [
            [ 1.0,         0.0, 0.0,         0.0,         0.0,         0.0,         0.0 ],
            [ 0.0,         0.0, 0.0,         0.0,         0.0,         0.0,         0.0 ],
            [ 0.373134328, 0.0, 0.358208955, 0.179104478, 0.074626866, 0.014925373, 0.0 ],
            [ 0.277108434, 0.0, 0.289156627, 0.301204819, 0.132530120, 0.0,         0.0 ],
            [ 0.042253521, 0.0, 0.126760563, 0.232394366, 0.542253521, 0.056338028, 0.0 ],
            [ 0.168421053, 0.0, 0.010526316, 0.126315789, 0.410526316, 0.284210526, 0.0 ],
            [ 0.176470588, 0.0, 0.058823529, 0.0,         0.235294118, 0.529411765, 0.0 ]
        ]

cb.update_params({"Parasite_Peak_Density_Probabilities": Transition_matrix})

if use_manual_scaling:

    immune_stim_threshold = len(Transition_matrix)
    #define a row scaling factor that represents the changing force of immunity across current density classes
    Row_scale_factor = []
    #define a column scaling factor that represents the changing force of immunity
    Column_scale_factor = []
else:
    #Not finished yet but this is where a RSM operator structure would live to be exposed during calibration
    operator = [[]]

# Add source of infection (challenge bite or forced EIR) --------------------------------------------------------
infect_by_EIR = 1

monthlyEIRs = [0.558,
0.348,
0.0975,
0.256,
1.435,
2.125,
1.0725,
0.299,
0.28,
0.77,
1.7575,
1.408,
]
#Values calculated as a product of the monthly HBR and SR data published in Kilama et al 2014 Malaria Journal https://doi.org/10.1186/1475-2875-13-111
if infect_by_EIR:
    add_InputEIR(cb, monthlyEIRs)
else:
    add_challenge_trial(cb,start_day=0)

# ---- CUSTOM REPORTS ----
add_patient_report(cb)

# Run args
run_sim_args = {'config_builder': cb,
                'exp_name': exp_name
                }

if __name__ == "__main__":

    SetupParser.default_block = 'LOCAL'
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    # Wait for the simulations to be done
    exp_manager.wait_for_finished(verbose=True)
    assert (exp_manager.succeeded())

