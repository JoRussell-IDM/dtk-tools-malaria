from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from dtk.utils.reports.VectorReport import add_human_migration_report
from malaria.reports.MalariaReport import add_event_counter_report, add_filtered_spatial_report
from dtk.interventions.health_seeking import add_health_seeking

from configure_forest_system import configure_forest_system


# General
exp_name = 'example_forest'
years = 1  # length of simulation, in years
serialization_path = '//internal.idm.ctr/IDM/home/jgerardin/input/Examples'
report_migration = False

village_nodes = [1,2]
forest_nodes = [3]


# Setup ----------------------------------------------------------------------------------------------------------
cb = configure_forest_system(years)
cb.update_params( {
    'Config_Name' : exp_name,
    'Serialized_Population_Filenames': ['serialized_forest.dtk'],
    'Serialized_Population_Path' : serialization_path
})

# Add case management --------------------------------------------------------------------------------------------
add_health_seeking(cb, start_day=0,
                   drug=['Artemether', 'Lumefantrine'],
                   nodes={"class": "NodeSetNodeList", "Node_List": village_nodes},
                   targets=[
                       {'trigger': 'NewClinicalCase', 'coverage': 0.4, 'agemin': 0, 'agemax': 5, 'seek': 1,
                        'rate': 0.3},
                       {'trigger': 'NewClinicalCase', 'coverage': 0.2, 'agemin': 5, 'agemax': 100, 'seek': 1,
                        'rate': 0.3},
                       {'trigger': 'NewSevereCase', 'coverage': 0.5, 'agemin': 0, 'agemax': 100, 'seek': 1,
                        'rate': 0.3}]
                   )


# ---- CUSTOM REPORTS ----
add_filtered_spatial_report(cb, start=365*(years-1), end=365*years,
                            channels=['Population', 'Prevalence', 'Adult_Vectors', 'PfHRP2_Prevalence',
                                      # 'PCR_Prevalence',
                                      'Daily_Bites_Per_Human', 'New_Infections', 'Daily_EIR'])
event_trigger_list=['Received_Treatment']
add_event_counter_report(cb, event_trigger_list=event_trigger_list)
if report_migration:
    add_human_migration_report(cb)

# Run args
run_sim_args = {'config_builder': cb,
                'exp_name': exp_name
                }

if __name__ == "__main__":

    SetupParser.default_block = 'HPC'

    SetupParser.init()
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    # Wait for the simulations to be done
    exp_manager.wait_for_finished(verbose=True)
    assert (exp_manager.succeeded())
