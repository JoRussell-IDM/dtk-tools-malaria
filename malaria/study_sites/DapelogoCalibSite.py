import logging
from collections import OrderedDict

import numpy as np
from calibtool.analyzers.Helpers import season_channel_age_density_json_to_pandas
from calibtool.study_sites.site_setup_functions import \
    config_setup_fn, summary_report_fn, add_treatment_fn, site_input_eir_fn

from calibtool.study_sites.DensityCalibSite import DensityCalibSite

logger = logging.getLogger(__name__)


class DapelogoCalibSite(DensityCalibSite):

    metadata = {
        'parasitemia_bins': [0, 50, 500, 5000, 50000, np.inf],  # (, 0] (0, 50] ... (50000, ]
        'age_bins': [5, 15, np.inf],  # (, 5] (5, 15] (15, ]

        'seasons_by_month': {  # Collection dates from raw data in Ouedraogo et al. JID 2015
            'July': 'start_wet',  # 29 June - 30 July '07 => [180 - 211]
            'September': 'peak_wet',  # 3 Sept - 9 Oct '07 => [246 - 282]
            'January': 'end_wet'  # (a.k.a. DRY) 10 Jan - 2 Feb '08 => [10 - 33]
        }
    }

    reference_dict = {

        # Digitized by J.Gerardin from data in:
        #   - A.L.Ouedraogo et al. JID 2015
        # for J.Gerardin et al. Malaria Journal 2015, 14:231
        # N.B. the values represent counts of individual observations

        "start_wet": {
            "Smeared True PfPR by Parasitemia and Age Bin": [
                [1, 0, 0, 2, 2, 3],
                [2, 1, 0, 2, 0, 4],
                [9, 5, 4, 4, 2, 3]
            ],
            "Smeared True PfPR by Gametocytemia and Age Bin": [
                [0, 1, 4, 2, 2, 0],
                [0, 1, 4, 6, 0, 0],
                [12, 8, 3, 4, 0, 0]
            ]
        },
        "peak_wet": {
            "Smeared True PfPR by Parasitemia and Age Bin": [
                [1, 2, 0, 1, 3, 1],
                [2, 5, 2, 3, 1, 1],
                [6, 8, 4, 4, 0, 2]
            ],
            "Smeared True PfPR by Gametocytemia and Age Bin": [
                [1, 3, 2, 2, 0, 0],
                [0, 8, 0, 3, 0, 0],
                [11, 10, 2, 2, 0, 0]
            ]
        },
        "end_wet": {
            "Smeared True PfPR by Parasitemia and Age Bin": [
                [1, 1, 0, 4, 3, 1],
                [4, 1, 2, 4, 2, 1],
                [6, 9, 6, 2, 2, 0]
            ],
            "Smeared True PfPR by Gametocytemia and Age Bin": [
                [2, 3, 2, 2, 1, 0],
                [2, 5, 4, 2, 1, 0],
                [14, 7, 4, 0, 0, 0]
            ]
        }
    }

    def get_reference_data(self, reference_type):
        super(DapelogoCalibSite, self).get_reference_data(reference_type)

        reference_bins = OrderedDict([
            ('Age Bin', self.metadata['age_bins']),
            ('PfPR Bin', self.metadata['parasitemia_bins'])
        ])
        reference_data = season_channel_age_density_json_to_pandas(self.reference_dict, reference_bins)

        return reference_data

    def get_setup_functions(self):
        setup_fns = super(DapelogoCalibSite, self).get_setup_functions()
        setup_fns.append(config_setup_fn(duration=365 * 5 + 1))  # 60 years (with leap years)
        setup_fns.append(summary_report_fn(interval=365.0/12, description='Monthly_Report',
                                           # parasitemia_bins=[0, 50, 500, 5000, 50000, 5000000],
                                           parasitemia_bins=[0, 50, 500, 5000, 50000, 5000000],
                                           age_bins=[5, 15, 100]))
        # setup_fns.append(add_treatment_fn(start=0, drug=['Artemether'],
        #                                   targets=[{'trigger': 'NewClinicalCase',
        #                                             'coverage': 1, 'seek': 0.15, 'rate': 0.3}]))
        setup_fns.append(site_input_eir_fn(self.name, birth_cohort=True))
        setup_fns.append(lambda cb: cb.update_params({'Demographics_Filenames': [
            'Calibration\\birth_cohort_demographics.compiled.json']}))

        return setup_fns

    def __init__(self):
        super(DapelogoCalibSite, self).__init__('Dapelogo')

