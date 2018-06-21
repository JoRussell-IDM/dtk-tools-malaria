import os
from examples.magude_multinode.core_magude_config_builder import CoreMagudeConfigBuilder
from simtools.SetupParser import SetupParser
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory


if __name__ == '__main__':
    # Key run parameters:
    base_path = "C:/Users/jsuresh/Code/dtk-tools-malaria/examples/magude_multinode/"
    sim_start_date = "2010-01-01"
    sim_length_days = 365*10 # Run for 10 years
    run_priority = "AboveNormal"
    run_coreset = "emod_32cores"
    experiment_name = "CoreMagude_Test"

    # Executable, inputs, dlls
    path_to_exe = os.path.join(base_path, "inputs/bin/Eradication.exe")
    dll_files_root = os.path.join(base_path, "inputs/bin/")
    input_files_root = os.path.join(base_path, "inputs/")


    # Intervention input files:
    healthseek_filename = os.path.join(base_path,"inputs/grid_all_healthseek_events.csv")
    itn_filename = os.path.join(base_path,"inputs/grid_all_itn_events.csv")
    irs_filename = os.path.join(base_path, "inputs/grid_all_irs_events.csv")
    mda_filename = os.path.join(base_path,"inputs/grid_all_mda_events.csv")
    rcd_filename = os.path.join(base_path,"inputs/grid_all_rcd_events.csv")

    mozamb_builder = CoreMagudeConfigBuilder(sim_start_date,
                                             sim_length_days,
                                             path_to_exe = path_to_exe,
                                             dll_files_root = dll_files_root,
                                             input_files_root = input_files_root,
                                             healthseek_filename = healthseek_filename,
                                             itn_filename = itn_filename,
                                             irs_filename = irs_filename,
                                             mda_filename = mda_filename,
                                             rcd_filename = rcd_filename
                                             )

    # Mozamb_builder generates the relevant config-builder
    cb = mozamb_builder.cb

    # Draw from serialized file that is in input.  This is a serialized file run from a calibrated burnin
    cb.update_params({
        "Serialized_Population_Path": "//internal.idm.ctr/IDM/home/jsuresh/input/Magude_Core_Geography_Example/", #input_files_root,
        'Serialized_Population_Filenames': ['state-00000-000.dtk','state-00000-001.dtk']
    })
    # Currently, serialization files can only be staged from COMPS


    # Start the simulation
    SetupParser.init()

    SetupParser.set("HPC", "priority", run_priority)
    SetupParser.set("HPC", "node_group", run_coreset)

    # Note: run set up to use 2 cores (to draw from the 2 serialized files)
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(config_builder=cb, exp_name=experiment_name)