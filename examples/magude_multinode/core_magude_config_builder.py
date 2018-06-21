# Simplified version of the Magude config builder, as a core geography example.

import os
import math
import numpy as np
import seaborn as sns
import pandas as pd
from dtk.interventions.health_seeking import add_health_seeking
from dtk.interventions.itn_age_season import add_ITN_age_season
from dtk.interventions.input_EIR import add_InputEIR
from dtk.interventions.irs import add_IRS
from malaria.interventions.malaria_drug_campaigns import add_drug_campaign

from malaria.reports.MalariaReport import add_filtered_report, add_event_counter_report, add_filtered_spatial_report

from dtk.vector.species import set_species_param

from spatial_sims.gridded_config_builder import GriddedConfigBuilder
from helpers.relative_time import *
from helpers.parse_demographics_file import get_ids_from_demographics_file
from spatial_sims.spatial_helpers import generate_birthnets_df_from_itn_event_file

#fixme For v2.0, use MSF-specific intervention files

class CoreMagudeConfigBuilder(GriddedConfigBuilder):

    def __init__(self,
                 sim_start_date,
                 sim_length_days,
                 path_to_exe=None,
                 dll_files_root=None,
                 input_files_root=None,
                 healthseek_filename=None,
                 itn_filename=None,
                 irs_filename=None,
                 mda_filename=None,
                 rcd_filename=None,
                 regional_EIR_node_label=100000,
                 regional_EIR_node_lat=-25.045777,
                 regional_EIR_node_lon=32.786861,
                 regional_EIR_scale_factor=0.5):

        self.healthseek_filename = healthseek_filename
        self.itn_filename = itn_filename
        self.irs_filename = irs_filename
        self.mda_filename = mda_filename
        self.rcd_filename = rcd_filename

        self.regional_EIR_node_label = regional_EIR_node_label
        self.regional_EIR_node_lat = regional_EIR_node_lat
        self.regional_EIR_node_lon = regional_EIR_node_lon
        self.regional_EIR_scale_factor = regional_EIR_scale_factor

        super().__init__(sim_start_date,
                         sim_length_days,
                         path_to_exe=path_to_exe,
                         dll_files_root=dll_files_root,
                         input_files_root=input_files_root,
                         num_cores=2,
                         demo_fp='demo.json',
                         local_migration_on=True,
                         use_climate_files=True,
                         climate_region="Mozambique",
                         verbose=True)


        self.filter_time_start = 0
        self.filter_length_days = 365*10
        self.catch = "Magude-Sede-Facazissa"
        self.demo_cells = get_ids_from_demographics_file(os.path.join(self.input_files_root, self.demo_fp))

        self.mozambique_setup()


    def mozambique_setup(self):
        self.africa_setup(self.cb)

        # Local migration amplitude:
        self.cb.update_params({
            "x_Local_Migration": 4
        })

        # NOTE: do not need to specify entomology parameters in cb because these are drawn directly from the serialized file
        # This makes the config file, unfortunately, confusing, because its entomology parameters are not relevant.
        # However, they ARE necessary otherwise DTK will complain that no species are using the LINEAR_SPLINE habitat
        self.add_ento_to_cb()
        # Regional migration node
        self.add_regional_EIR_node()
        self.implement_interventions()


    def add_ento_to_cb(self):
        # Vector properties:
        self.cb.update_params({'Vector_Species_Names': ['arabiensis', 'funestus']})

        # Arabiensis
        set_species_param(self.cb, 'arabiensis', 'Indoor_Feeding_Fraction', 0.5)
        set_species_param(self.cb, 'arabiensis', 'Adult_Life_Expectancy', 20)
        set_species_param(self.cb, 'arabiensis', 'Anthropophily', 0.65)
        set_species_param(self.cb, 'arabiensis', 'Larval_Habitat_Types',
                          {
                              "LINEAR_SPLINE": {
                                  "Capacity_Distribution_Number_Of_Years": 1,
                                  "Capacity_Distribution_Over_Time": {
                                      "Times": [0.0, 30.417, 60.833, 91.25, 121.667, 152.083, 182.5, 212.917,
                                                243.333, 273.75, 304.167, 334.583],
                                      "Values": [1] * 12
                                  },
                                  "Max_Larval_Capacity": pow(10, 9.88)
                              }
                          })

        # Funestus
        set_species_param(self.cb, 'funestus', "Indoor_Feeding_Fraction", 0.9)
        set_species_param(self.cb, 'funestus', 'Adult_Life_Expectancy', 20)
        set_species_param(self.cb, 'funestus', 'Anthropophily', 0.65)
        set_species_param(self.cb, 'funestus', 'Larval_Habitat_Types', {
            "WATER_VEGETATION": 2e3,
            "LINEAR_SPLINE": {
                "Capacity_Distribution_Number_Of_Years": 1,
                "Capacity_Distribution_Over_Time": {
                    "Times": [0.0, 30.417, 60.833, 91.25, 121.667, 152.083, 182.5, 212.917, 243.333, 273.75,
                              304.167, 334.583],

                    "Values": [1] * 12
                },
                "Max_Larval_Capacity": pow(10, 10.60)
            }
        })


    def add_regional_EIR_node(self):
        # From Jaline
        self.cb.update_params({
            'Enable_Regional_Migration': 1,
            'Regional_Migration_Roundtrip_Duration': 3,
            'Regional_Migration_Roundtrip_Probability': 1,
            'x_Regional_Migration': 0.0405,
            'Regional_Migration_Filename': 'regional_migration.bin',
        })

        monthly_profile = [12.1, 23.9, 33.5, 14.8, 6.8, 4.9, 3.3, 3.8, 3.5, 3.3, 2.8, 4.3]
        add_InputEIR(self.cb,
                     monthlyEIRs=[x * self.regional_EIR_scale_factor for x in monthly_profile],
                     nodes={'class': 'NodeSetNodeList', 'Node_List': [self.regional_EIR_node_label]},
                     start_day=0)


        # Add filtered reports to separate this node out
        add_filtered_report(self.cb, nodes=[self.regional_EIR_node_label], description='Work')
        all_catch_nodes = get_ids_from_demographics_file(os.path.join(self.input_files_root,self.demo_fp))
        all_catch_nodes.remove(self.regional_EIR_node_label)
        add_filtered_report(self.cb, nodes= all_catch_nodes, description='Catchment')


    #################################################################################################
    # INTERVENTIONS (ADDITIONS TO CAMPAIGN FILE)

    def add_healthseeking(self):
        # Implement basic health-seeking behavior for all individuals in simulation

        # Event information files
        healthseek_events = pd.read_csv(self.healthseek_filename)
        healthseek_events['simday'] = [convert_to_day(x, self.sim_start_date, "%Y-%m-%d") for x in
                                       healthseek_events.fulldate]
        healthseek_events = healthseek_events[np.in1d(healthseek_events['grid_cell'], self.demo_cells)]
        healthseek_events.reset_index(inplace=True, drop=True)

        [binned_and_grouped, grouped_by_fields]  = self.try_campaign_compression(healthseek_events)

        for tup, group in binned_and_grouped:
            table = self.convert_group_tuple_to_dict(tup, grouped_by_fields)
            node_list = list(group['grid_cell'])
            if sorted(node_list) == self.demo_cells:
                node_dict = {"class": "NodeSetAll"}
            else:
                node_dict = {"class": "NodeSetNodeList", "Node_List": node_list}

            add_health_seeking(self.cb,
                               start_day=float(table['simday']),
                               targets=[{'trigger': 'NewClinicalCase',
                                         'coverage': float(table['cov_newclin_youth']),
                                         'agemin': 0,
                                         'agemax': 5,
                                         'seek': 1,
                                         'rate': 0.3},
                                        {'trigger': 'NewClinicalCase',
                                         'coverage': float(table['cov_newclin_adult']),
                                         'agemin': 5,
                                         'agemax': 100,
                                         'seek': 1,
                                         'rate': 0.3},
                                        {'trigger': 'NewSevereCase',
                                         'coverage': float(table['cov_severe_youth']),
                                         'agemin': 0,
                                         'agemax': 5,
                                         'seek': 1, 'rate': 0.5},
                                        {'trigger': 'NewSevereCase',
                                         'coverage': float(table['cov_severe_adult']),
                                         'agemin': 5,
                                         'agemax': 100,
                                         'seek': 1,
                                         'rate': 0.5}],
                               drug=['Artemether', 'Lumefantrine'],
                               dosing='FullTreatmentNewDetectionTech',
                               nodes=node_dict,
                               duration=float(table['duration']))


    def add_itns(self):
        # Add ITN events:
        itn_events_list = ["Bednet_Got_New_One","Bednet_Using","Bednet_Discarded"]
        self.cb.update_params({
            "Report_Event_Recorder_Ignore_Events_In_List": 0,
            "Listed_Events": itn_events_list,
            "Report_Event_Recorder_Events": [],
            "Report_Event_Recorder": 1
        })

        itn_events = pd.read_csv(self.itn_filename)
        itn_events['simday'] = [convert_to_day(x, self.sim_start_date, "%Y-%m-%d") for x in itn_events.fulldate]
        itn_events = itn_events[np.in1d(itn_events['grid_cell'], self.demo_cells)]
        itn_events.reset_index(inplace=True, drop=True)
        itn_events = itn_events[['event','fulldate','cov_all','age_cov','min_season_cov','fast_fraction','grid_cell','simday']]

        birthnet_events = generate_birthnets_df_from_itn_event_file(itn_events)
        birthnet_events = birthnet_events[['event','fulldate','cov_all','age_cov','min_season_cov','fast_fraction','grid_cell','simday','duration']]

        [binned_and_grouped, grouped_by_fields] = self.try_campaign_compression(itn_events[itn_events['simday'] >= 0])

        for tup, group in binned_and_grouped:
            table = self.convert_group_tuple_to_dict(tup, grouped_by_fields)
            node_list = list(group['grid_cell'])
            if sorted(node_list) == self.demo_cells:
                nodeIDs = []
            else:
                nodeIDs = node_list

            # Regular bednet distribution
            cov_all = float(table['cov_all'])
            if cov_all > 0:
                add_ITN_age_season(self.cb,
                                   start=float(table['simday']),
                                   age_dep={'youth_cov': float(table['age_cov']),
                                            'youth_min_age': 5,
                                            'youth_max_age': 20},
                                   coverage_all=float(table['cov_all']),
                                   as_birth=False,
                                   seasonal_dep={'min_cov': float(table['min_season_cov']),
                                                 'max_day': 1},
                                   discard={'halflife1': 260,
                                            'halflife2': 2106,
                                            'fraction1': float(table['fast_fraction'])},
                                   nodeIDs=nodeIDs)

        # Separately handle birth nets:
        [binned_and_grouped, grouped_by_fields] = self.try_campaign_compression(birthnet_events[birthnet_events['simday'] >= 0])
        for tup, group in binned_and_grouped:
            table = self.convert_group_tuple_to_dict(tup, grouped_by_fields)
            node_list = list(group['grid_cell'])
            if sorted(node_list) == self.demo_cells:
                nodeIDs = []
            else:
                nodeIDs = node_list

            cov_all = float(table['cov_all'])
            if cov_all > 0:
                add_ITN_age_season(self.cb,
                                   start=float(table['simday']),
                                   age_dep={'youth_cov': float(table['age_cov']), 'youth_min_age': 5,
                                            'youth_max_age': 20},
                                   coverage_all=float(table['cov_all']),
                                   seasonal_dep={'min_cov': float(table['min_season_cov']), 'max_day': 60},
                                   discard={'halflife1': 260,
                                            'halflife2': 2106,
                                            'fraction1': float(table['fast_fraction'])},
                                   nodeIDs=nodeIDs,
                                   as_birth=True,
                                   duration=table['duration'])





    def add_irs(self):
        irs_events = pd.read_csv(self.irs_filename)
        irs_events['simday'] = [convert_to_day(x, self.sim_start_date, "%Y-%m-%d") for x in irs_events.fulldate]
        irs_events = irs_events[np.in1d(irs_events['grid_cell'], self.demo_cells)]
        irs_events.reset_index(inplace=True, drop=True)
        irs_events = irs_events[['grid_cell','event','fulldate','simday','cov_all','killing','exp_duration','box_duration']]

        [binned_and_grouped, grouped_by_fields] = self.try_campaign_compression(irs_events)

        for tup, group in binned_and_grouped:
            table = self.convert_group_tuple_to_dict(tup, grouped_by_fields)
            node_list = list(group['grid_cell'])
            if sorted(node_list) == self.demo_cells:
                nodeIDs = []
            else:
                nodeIDs = node_list

            cov_all = float(table['cov_all'])
            if cov_all > 0:
                add_IRS(self.cb,
                        start=int(table['simday']),
                        coverage_by_ages=[{'coverage': float(table['cov_all'])}],
                        waning={"Killing_Config": {
                            "Initial_Effect": float(table['killing']),
                            "Decay_Time_Constant": float(table['exp_duration']),
                            "Box_Duration": float(table['box_duration']),
                            "class": "WaningEffectBoxExponential"
                        }},
                        nodeIDs=nodeIDs)


    def add_mda(self):
        mda_events = pd.read_csv(self.mda_filename)
        mda_events['simday'] = [convert_to_day(x, self.sim_start_date, "%Y-%m-%d") for x in mda_events.fulldate]
        mda_events = mda_events[np.in1d(mda_events['grid_cell'], self.demo_cells)]
        mda_events.reset_index(inplace=True, drop=True)
        mda_events = mda_events[['grid_cell','event','fulldate','simday','cov_all']]

        [binned_and_grouped, grouped_by_fields] = self.try_campaign_compression(mda_events)

        for tup, group in binned_and_grouped:
            table = self.convert_group_tuple_to_dict(tup, grouped_by_fields)
            node_list = list(group['grid_cell'])
            if sorted(node_list) == self.demo_cells:
                nodeIDs = []
            else:
                nodeIDs = node_list

            cov_all = float(table['cov_all'])
            if cov_all > 0:
                add_drug_campaign(self.cb,
                                  campaign_type='MDA',
                                  drug_code='DP',
                                  start_days=[float(table['simday'])],
                                  coverage=float(table['cov_all']),
                                  repetitions=1,
                                  interval=60,
                                  nodes=nodeIDs)


    def add_rcd(self):
        rcd_events = pd.read_csv(self.rcd_filename)
        rcd_events['simday'] = [convert_to_day(x, self.sim_start_date, "%Y-%m-%d") for x in rcd_events.fulldate]
        rcd_events = rcd_events[np.in1d(rcd_events['grid_cell'], self.demo_cells)]
        rcd_events.reset_index(inplace=True, drop=True)
        rcd_events = rcd_events[['grid_cell','event','fulldate','simday','coverage','trigger_coverage','interval']]

        [binned_and_grouped, grouped_by_fields] = self.try_campaign_compression(rcd_events)

        for tup, group in binned_and_grouped:
            table = self.convert_group_tuple_to_dict(tup, grouped_by_fields)
            node_list = list(group['grid_cell'])
            if sorted(node_list) == self.demo_cells:
                nodeIDs = []
            else:
                nodeIDs = node_list

            coverage = float(table['coverage'])
            if coverage > 0:
                add_drug_campaign(self.cb,
                                  campaign_type='rfMSAT',
                                  drug_code='AL',
                                  start_days=[float(table['simday'])],
                                  coverage=float(table['coverage']),
                                  trigger_coverage=float(table['trigger_coverage']),
                                  interval=float(table['interval']),
                                  nodes=nodeIDs)


    def convert_group_tuple_to_dict(self, tup, field_names):
        return_dict = {}

        for i in range(len(field_names)):
            return_dict[field_names[i]] = tup[i]
        return return_dict


    def try_campaign_compression(self, intervention_df, bin_fidelity=0.05):
        # Because implementing things on a grid_cell level leads to enormous campaign files, try to group things together wherever possible
        def round_nearest(x, a):
            rounded = round(round(x / a) * a, -int(math.floor(math.log10(a))))
            return rounded

        binned_intervention_df = intervention_df.copy(deep=True)

        # Bin all fields other than grid_cell and date:
        field_list = list(intervention_df.columns)
        field_list.remove('grid_cell')
        field_list.remove('fulldate')
        field_list.remove('simday')

        # Bin these fields with bin width = bin_fidelity
        for field in field_list:
            binned_intervention_df[field] = intervention_df[field].map(lambda x: round_nearest(x, bin_fidelity))

        # Group by the new binned fields, as well as by date
        grouped_by_fields = ['simday'] + field_list
        binned_and_grouped = binned_intervention_df.groupby(grouped_by_fields)

        return [binned_and_grouped, grouped_by_fields]


    def implement_interventions(self):
        self.add_healthseeking()
        self.add_itns()
        self.add_irs()
        self.add_mda()
        self.add_rcd()
