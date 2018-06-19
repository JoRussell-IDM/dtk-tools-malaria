from calibtool.study_sites.site_setup_functions import summary_report_fn
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.species import set_species_param
from dtk.generic.climate import set_climate_constant
from createSimDirectoryMapBR import createSimDirectoryMap
from malaria.interventions.malaria_drug_campaigns import add_drug_campaign
from dtk.interventions.ivermectin import add_ivermectin
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder, ModFn
from simtools.SetupParser import SetupParser
from update_drug_params import update_drugs

import pandas as pd
import os


def add_ivermectin_group(cb, coverage=1.0, start_days=[60, 60+365], drug_code=30, smc_code='DP5'):
    '''
    This function sets up an ivermectin campaign where people who have received SMC drugs also receive ivermectin
    :param cb: config builder
    :param coverage: coverage for Ivermectin
    :param start_days: campaign start day
    :param drug_code: Ivermectin drug code
    :param smc_code: SMC campaign type (under 5: DP5, under 10: DP 10 etc.)
    :return: Ivermectin tags
    '''

    add_ivermectin(cb, drug_code=drug_code, coverage=coverage, start_days=start_days,
                   trigger_condition_list=['Received_Campaign_Drugs'])

    return {'Intervention_type': '%s+IV_%i' % (smc_code, drug_code)}


def add_smc_group(cb, coverage=1.0, start_days=[60, 60+365], agemax=10, drug='DP', dp_gam_kill_on=1):
    '''
    This function sets up an SMC campaign for children under a certain age. Drug parameters can be changed to include or exclude gametocyte killing.
    :param cb: config builder
    :param coverage: coverage for SMC
    :param start_days: campaign start day
    :param agemax: children under this age will receive SMC drugs
    :param drug: type of drug to be used in SMC campaign
    :param dp_gam_kill_on: turn on or off gametocyte killing of drug
    :return: tags for SMC campaign
    '''

    add_drug_campaign(cb, 'SMC', drug, start_days=start_days, repetitions=3, interval=30,
    coverage=coverage,
    target_group={'agemin': 0, 'agemax': agemax})

    if not dp_gam_kill_on:
        malaria_drug_params = update_drugs(['DHA', 'Drug_Gametocyte02_Killrate'], 0.0)
        malaria_drug_params = update_drugs(['DHA', 'Drug_Gametocyte34_Killrate'], 0.0,
                                           malaria_drug_params=malaria_drug_params)
        malaria_drug_params = update_drugs(['DHA', 'Drug_GametocyteM_Killrate'], 0.0,
                                           malaria_drug_params=malaria_drug_params)
        malaria_drug_params = update_drugs(['Piperaquine', 'Drug_Gametocyte02_Killrate'], 0.0,
                                           malaria_drug_params=malaria_drug_params)

        cb.update_params({"Malaria_Drug_Params": malaria_drug_params})

    return {'Coverage': coverage, 'Start': start_days[0], 'Intervention_type': 'SMC%i' %agemax}


def add_summary_report(cb, start_day=0):
    '''
    Add daily summary report to output
    :param cb: config builder
    :param start_day: start day for report
    :return: None
    '''

    summary_report_fn(start=start_day+1, interval=1.0, description='Daily_Report',
                      age_bins=[5.0, 10.0, 100.0])(cb)

    return None


def make_simmap(expname):
    '''
    Creates a dataframe of all simulation in a given experiment on COMPS
    :param expname: ID for experiment
    :return: dataframe of simulations with tags
    '''

    simmap = createSimDirectoryMap(expname)

    return simmap


# Get filelist of files in simmap
def get_filepath(simmap, filetype='state-'):
    '''

    :param simmap: dataframe of simulations with tags
    :param filetype: type of file from output (Inset chart, Summary chart etc etc.)
    :return: dataframe of simulations with request output file for each sim
    '''

    filelist = []
    for path in simmap['outpath']:
        outputpath = os.path.join(path, 'output')
        for file in os.listdir(outputpath):
            if filetype in file:
                filelist.append(os.path.join(outputpath, file))

    simmap['filelist'] = filelist

    return simmap


def get_outpath_for_serialized_file(simmap, seed):
    '''
    :param simmap: dataframe of simulations with tags
    :param seed: seed number of simulation for which filepath is requested
    :return: filepath of serialized file
    '''

    temp = simmap[simmap['Run_Number'] == seed]

    return temp[temp['Run_Number'] == seed]['outpath'].values[0]


if __name__ == "__main__":

    sim_duration = 365 * 1
    num_seeds = 50

    expname = 'single_node_example_with_interventions'

    SetupParser.init('HPC')

    cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

    intervention_days = [180]
    coverages = [0.6, 0.7, 0.8, 0.9, 1.0]

    # Experiment id for serialized file
    exp_name = ['5285e27c-9063-e811-a2c0-c4346bcb7275']

    for exp in exp_name:
        temp_sim_map = make_simmap(exp, filetype='Inset')
        if 'sim_map' not in locals():
            sim_map = temp_sim_map
        else:
            sim_map = pd.concat([sim_map, temp_sim_map])

    # DP only (expanded and regular)
    SMC1 = [
                [
                   ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed),
                   ModFn(DTKConfigBuilder.set_param, 'Simulation_Duration', smc_start_day+365),
                   ModFn(add_smc_group,
                             start_days=[smc_start_day],
                             coverage=smc_coverage, drug=drug, agemax=agemax, dp_gam_kill_on=1),
                   ModFn(add_summary_report, start_day=smc_start_day),
                   ModFn(DTKConfigBuilder.set_param, 'Serialized_Population_Path',
                          '{path}/output'.format(path=
                                                 get_outpath_for_serialized_file(simmap, seed)))
                ]
               for smc_start_day in intervention_days
               for smc_coverage in coverages
               for seed in range(num_seeds)
               for simmap in [sim_map]
               for agemax in [5, 10]
               for drug in ['DP']
            ]

    # DP + Ivermectin (expanded and regular)
    SMC3 = [
        [
            ModFn(DTKConfigBuilder.set_param, 'Run_Number', seed),
            ModFn(DTKConfigBuilder.set_param, 'Simulation_Duration', smc_start_day + 365),
            ModFn(add_smc_group,
                  start_days=[smc_start_day],
                  coverage=smc_coverage, drug=drug, agemax=agemax, dp_gam_kill_on=1),
            ModFn(add_ivermectin_group, start_days=[smc_start_day], drug_code=drug_code, smc_code=drug + str(agemax)),
            ModFn(add_summary_report, start_day=smc_start_day),
            ModFn(DTKConfigBuilder.set_param, 'Serialized_Population_Path',
                  '{path}/output'.format(path=
                                         get_outpath_for_serialized_file(simmap, seed)))
        ]
        for smc_start_day in intervention_days
        for smc_coverage in coverages
        for seed in range(num_seeds)
        for simmap in [sim_map]
        for agemax in [5, 10]
        for drug in ['DP']
        for drug_code in [30, 90]
    ]

    builder = ModBuilder.from_list(SMC1+SMC3)

    set_climate_constant(cb)
    set_species_param(cb, 'gambiae', 'Larval_Habitat_Types',
                      {"LINEAR_SPLINE": {
                          "Capacity_Distribution_Per_Year": {
                              "Times": [0.0, 30.417, 60.833, 91.25, 121.667, 152.083,
                                        182.5, 212.917, 243.333, 273.75, 304.167, 334.583],
                              "Values": [3, 0.8,  1.25, 0.1,  2.7, 8, 4, 35, 6.8,  6.5, 2.6, 2.1]
                          },
                          "Max_Larval_Capacity": 1e9
                      }})
    set_species_param(cb, "gambiae", "Indoor_Feeding_Fraction", 0.9)
    set_species_param(cb, "gambiae", "Adult_Life_Expectancy", 20)

    cb.update_params({"Demographics_Filenames": ['single_node_demographics.json'],

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

                      'Falciparum_MSP_Variants': 32,
                      'Falciparum_Nonspecific_Types': 76,
                      'Falciparum_PfEMP1_Variants': 1070,
                      'Gametocyte_Stage_Survival_Rate': 0.588569307,

                      'MSP1_Merozoite_Kill_Fraction': 0.511735322,
                      'Max_Individual_Infections': 3,
                      'Nonspecific_Antigenicity_Factor': 0.415111634,

                      'x_Temporary_Larval_Habitat': 0.2,
                      'logLevel_default': 'ERROR',

                      "Simulation_Duration": sim_duration,
                      "Serialization_Test_Cycles": 0,
                      'Serialized_Population_Filenames': ['state-21900.dtk'],
                      "Vector_Species_Names": ['gambiae']
                      })

    run_sim_args = {'config_builder': cb,
                    'exp_name': expname,
                    'exp_builder': builder}

    exp_manager = ExperimentManagerFactory.from_setup()
    exp_manager.run_simulations(**run_sim_args)
    exp_manager.wait_for_finished(verbose=True)
