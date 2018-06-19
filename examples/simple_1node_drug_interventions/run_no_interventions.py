from calibtool.study_sites.site_setup_functions import summary_report_fn
from dtk.interventions.health_seeking import add_health_seeking
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.species import set_species_param
from dtk.generic.climate import set_climate_constant
from createSimDirectoryMapBR import createSimDirectoryMap
from simtools.DataAccess.ExperimentDataStore import ExperimentDataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder, ModFn
from simtools.SetupParser import SetupParser
import pandas as pd


def make_simmap(expname):

    simmap = createSimDirectoryMap(expname)
    # simmap = get_filepath(simmap, filetype)

    return simmap


def add_summary_report(cb, start_day=0):

    summary_report_fn(start=start_day+1, interval=1.0, description='Daily_Report',
                      age_bins=[5.0, 10.0, 100.0])(cb)

    return None


def get_outpath_for_serialized_file(simmap, seed):

    temp = simmap[simmap['Run_Number'] == seed]

    return temp[temp['Run_Number'] == seed]['outpath'].values[0]


if __name__ == "__main__":

    expname = 'No_intervention_age_stratified_uncor_10y'

    sim_duration = 365 * 1
    num_seeds = 50           # 50

    intervention_days = [180]
    # intervention_days = [i for i in range(0, 366, 10)]
    # intervention_days = [i for i in range(195, 300, 1)]

    SetupParser('HPC')

    cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

    # serialization_exp_id = '8609dae7-a3a7-e711-9414-f0921c16b9e5'   # Homogeneous
    # expt = ExperimentDataStore.get_experiments(serialization_exp_id)
    # outpath = [sim.get_path() for exp in expt for sim in exp.simulations]
    # outpath = [
    #     '//internal.idm.ctr/IDM/Home/pselvaraj/output/Matsari_homogeneousbiting_serialization_2017_10_02_12_00_07_818000/89d/00c/08a/89d00c08-a4a7-e711-9414-f0921c16b9e5']
    exp_name = ['5285e27c-9063-e811-a2c0-c4346bcb7275']

    for exp in exp_name:
        temp_sim_map = make_simmap(exp)
        if 'sim_map' not in locals():
            sim_map = temp_sim_map
        else:
            sim_map = pd.concat([sim_map, temp_sim_map])

    builder = ModBuilder.from_list([
            [
             ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed),
             ModFn(DTKConfigBuilder.set_param, 'Simulation_Duration', start_day + 365),
             ModFn(add_summary_report, start_day=start_day),
             ModFn(DTKConfigBuilder.set_param, 'Serialized_Population_Path',
                      '{path}/output'.format(path=
                                             get_outpath_for_serialized_file(simmap, seed)))
            ]
            for seed in range(num_seeds)
            for simmap in [sim_map]
            for start_day in intervention_days]
    )

    # configure_dapelogo(cb)
    # cb.set_collection_id('1c189292-5471-e711-9401-f0921c16849d')
    set_climate_constant(cb)
    set_species_param(cb, 'gambiae', 'Larval_Habitat_Types',
                      {"LINEAR_SPLINE": {
                          "Capacity_Distribution_Per_Year": {
                              "Times": [0.0, 30.417, 60.833, 91.25, 121.667, 152.083,
                                        182.5, 212.917, 243.333, 273.75, 304.167, 334.583],
                              # "Values": [1, 0.25, 0.1, 1, 1, 0.5, 12, 5, 3, 2, 1.5, 1.5]
                              "Values": [3, 0.8,  1.25, 0.1,  2.7, 8, 4, 35, 6.8,  6.5, 2.6, 2.1]
                          },
                          "Max_Larval_Capacity": 1e9
                      }})
    set_species_param(cb, "gambiae", "Adult_Life_Expectancy", 20)
    set_species_param(cb, "gambiae", "Indoor_Feeding_Fraction", 0.9)

    cb.update_params({"Demographics_Filenames": ['Calibration\single_node_demographics.json'],

                      'Antigen_Switch_Rate': pow(10, -9.116590124),
                      'Base_Gametocyte_Production_Rate': 0.06150582,
                      'Base_Gametocyte_Mosquito_Survival_Rate': 0.002011099,
                      'Base_Population_Scale_Factor': 0.1,

                      "Birth_Rate_Dependence": "FIXED_BIRTH_RATE",
                      "Death_Rate_Dependence": "NONDISEASE_MORTALITY_BY_AGE_AND_GENDER",
                      "Disable_IP_Whitelist": 1,

                      "Enable_Vital_Dynamics": 1,
                      "Enable_Birth": 1,
                      'Enable_Default_Reporting': 1,
                      'Enable_Demographics_Other': 1,
                      # 'Enable_Property_Output': 1,

                      'Falciparum_MSP_Variants': 32,
                      'Falciparum_Nonspecific_Types': 76,
                      'Falciparum_PfEMP1_Variants': 1070,
                      'Gametocyte_Stage_Survival_Rate': 0.588569307,

                      'MSP1_Merozoite_Kill_Fraction': 0.511735322,
                      'Max_Individual_Infections': 3,
                      'Nonspecific_Antigenicity_Factor': 0.415111634,

                      'x_Temporary_Larval_Habitat': 1,
                      'logLevel_default': 'ERROR',

                      "Serialization_Test_Cycles": 0,
                      'Serialized_Population_Filenames': ['state-21900.dtk'],
                      # 'Serialized_Population_Path': '{path}/output'.format(path=outpath[0]),
                      "Vector_Species_Names": ['gambiae']
                      })

    # add_health_seeking(cb,
    #                    targets=[{'trigger': 'NewClinicalCase', 'coverage': 0.3, 'agemin': 5, 'agemax': 70, 'seek': 1.0,
    #                              'rate': 0.3},
    #                             {'trigger': 'NewClinicalCase', 'coverage': 0.5, 'agemin': 0, 'agemax': 5,
    #                              'seek': 1.0, 'rate': 0.3},
    #                             {'trigger': 'NewSevereCase', 'coverage': 0.5, 'seek': 1.0, 'rate': 0.5}],
    #                    drug=['Artemether', 'Lumefantrine'],
    #                    dosing='FullTreatmentNewDetectionTech',
    #                    nodes={"class": "NodeSetAll"},
    #                    repetitions=1,
    #                    tsteps_btwn_repetitions=365,
    #                    broadcast_event_name='Received_Treatment')
    #
    # from malaria.reports.MalariaReport import add_event_counter_report
    # add_event_counter_report(cb, ['Received_Treatment'])

    run_sim_args = {'config_builder': cb,
                    'exp_name': expname,
                    'exp_builder': builder}

    exp_manager = ExperimentManagerFactory.from_setup()
    exp_manager.run_simulations(**run_sim_args)
    exp_manager.wait_for_finished(verbose=True)
