import numpy as np
import pandas as pd
import os
import json
import matplotlib.pyplot as plt
import matplotlib as mpl

from createSimDirectoryMapBR import createSimDirectoryMap

mpl.rcParams['pdf.fonttype'] = 42


# Make simmap from COMPS
def make_simmap(expname, is_name=True, filetype='Inset'):

    simmap = createSimDirectoryMap(expname)
    simmap = get_filepath(simmap, filetype)

    return simmap


# Get simmap for specific rows listed in restrictions
def get_simmap_restricted(simmap, restrictions={}):

    for restriction in restrictions:
        simmap = simmap.loc[simmap[restriction] == restrictions[restriction]]

    return simmap


# Check if file exists in all output paths
def get_fileexist(simmap):

    fileexist = []
    for path in simmap['outpath']:
        outputpath = os.path.join(path, 'output')
        if not os.path.exists(outputpath):
            fileexist.append(0)
        else:
            fileexist.append(1)

    simmap['fileexist'] = fileexist
    simmap = simmap[simmap['fileexist'] == 1]
    del simmap['fileexist']

    return simmap


# Get filelist of files in simmap
def get_filepath(simmap, filetype='Inset'):

    filelist = []
    for path in simmap['outpath']:
        outputpath = os.path.join(path, 'output')
        for file in os.listdir(outputpath):
            if filetype in file:
                filelist.append(os.path.join(outputpath, file))

    simmap['filelist'] = filelist

    return simmap


# Get data from specific files and make dataframe
def get_data(simmap):

    directory = data_dir
    if not os.path.exists(directory):
        os.makedirs(directory)
    fileraw = os.path.join(directory, 'Prevalence_EIR_raw_inset.csv')

    if not os.path.exists(fileraw):

        filetemp = os.path.join(directory, 'Sim_temp_inset_data.csv')

        if not os.path.exists(filetemp):

            # Pull data from JSON file
            df = simmap.copy()
            listtodel = ['Serialized_Population_Path', 'exe_collection_id', 'dll_collection_id', 'input_collection_id',
                         'outpath', 'simid', 'add_summary_report.start_day']
            df = df.drop(listtodel, axis=1)
            df['Infections_reduced'] = [0] * len(df['filelist'])
            df['Annual_EIR'] = [0] * len(df['filelist'])

            for file in df['filelist']:
                with open(file) as fin:
                    datatemp = json.loads(fin.read())
                    df['Infections_reduced'].loc[df['filelist'] == file] = \
                        np.abs(1 - datatemp['Channels']['Infected']['Data'][-1]/datatemp['Channels']['Infected']['Data'][-365])
                    df['Annual_EIR'].loc[df['filelist'] == file] = \
                        np.sum(datatemp['Channels']['Daily EIR']['Data'][-365:])

            df = df.drop('filelist', axis=1)
            df = df.sort_values(df.columns.tolist()[:-2])
            df.to_csv(filetemp)

        else:
            df = pd.read_csv(filetemp)
            if 'Unnamed: 0' in df.columns:
                df = df.drop('Unnamed: 0', axis=1)

        # temp_data = get_no_intervention_data()
        #
        # for (group, group_df) in df.groupby(['Intervention_type'], as_index=False):
        #     ref_clinical = temp_data['Annual_EIR'].values[0]
        #     mask = list(group_df.index)
        #     templist = list(group_df['Annual_EIR'].apply(lambda x: ref_clinical - x))
        #     df['Annual_EIR'][mask] = templist

        df.to_csv(fileraw)

    else:
        df = pd.read_csv(fileraw)
    if 'Unnamed: 0' in df.columns:
        df = df.drop('Unnamed: 0', axis=1)
    if 'Unnamed: 0.1' in df.columns:
        df = df.drop('Unnamed: 0.1', axis=1)

    listtoavg = [e for e in list(df.columns.values) if e not in ('Run_Number', 'Infections_reduced', 'Annual_EIR')]
    df1 = df.groupby(listtoavg)['Infections_reduced'].apply(np.mean).reset_index()
    df1['Infections_reduced_std'] = list(df.groupby(listtoavg)['Infections_reduced'].apply(np.std))
    df1['Annual_EIR'] = list(df.groupby(listtoavg)['Annual_EIR'].apply(np.mean))
    df1['Annual_EIR_std'] = list(df.groupby(listtoavg)['Annual_EIR'].apply(np.std))

    directory = data_dir
    if not os.path.exists(directory):
        os.makedirs(directory)
    file = os.path.join(directory, 'Prevalence_EIR_across_runs_inset.csv')
    df1.to_csv(file)

    return df1


def get_ref_data(simmap):

    # Pull data from JSON file
    df = simmap.copy()
    listtodel = ['Serialized_Population_Path', 'exe_collection_id', 'dll_collection_id', 'input_collection_id',
                 'outpath', 'simid',
                 'add_summary_report.start_day']
    df = df.drop(listtodel, axis=1)
    annual_EIR = []

    directory = data_dir
    if not os.path.exists(directory):
        os.makedirs(directory)
    fileinset = os.path.join(directory, 'Reference_raw_inset.csv')

    if os.path.exists(fileinset):
        df = pd.read_csv(fileinset)
    else:
        for file in simmap['filelist']:
            with open(file) as fin:
                datatemp = json.loads(fin.read())
                # Sum of all cases for second year
                annual_EIR.append(np.sum(datatemp['Channels']['Daily EIR']['Data'][-365:]))
                # Number of infections at end of simulation

        df['Annual_EIR'] = annual_EIR
        df = df.drop('filelist', axis=1)
        df.to_csv(fileinset)

    if 'Unnamed: 0' in df.columns:
        df = df.drop('Unnamed: 0', axis=1)

    listtoavg = [e for e in list(df.columns.values) if e not in ('Run_Number', 'Annual_EIR')]
    df1 = df.groupby(listtoavg, as_index=False)['Annual_EIR'].mean()
    df1['Annual_EIR_std'] = list(df.groupby(listtoavg)['Annual_EIR'].apply(np.std))

    file = os.path.join(directory, 'Reference_averaged_across_runs_inset.csv')
    df1.to_csv(file)

    return df1


def get_no_intervention_data():

    directory = data_dir
    if not os.path.exists((directory)):
        os.mkdir(directory)

    file = os.path.join(directory, 'Reference_averaged_across_runs_inset.csv')

    if not os.path.exists(file):
        # exp = '2ab297ab-5961-e811-a2c0-c4346bcb7275'  # No intervention - 15y
        exp = 'f8091726-c968-e811-a2c0-c4346bcb7275'  # No intervention - 10y
        sim_map = make_simmap(exp, is_name=False, filetype='Inset')
        sim_map.to_csv(os.path.join(data_dir, 'Sim_map_reference_inset.csv'))

        data = get_ref_data(sim_map)
    else:
        data = pd.read_csv(file)

    return data


def plot_lines_with_shaded_areas(fig, df, dtype, ref=False, ylim=[], yerr=True, **kwargs):

    axes = fig.axes

    if not axes:
        fig.set_size_inches((15, 7))  # override smaller single-panel default from SiteDataPlotter
        axes = [fig.add_subplot(1, 1, 1)]

    intervention_colors = ['r', 'g', 'b', 'y', 'm']
    interventions = list(df['IRS_halflife'].unique())

    ax = axes[0]

    for iax, (intervention, group_df) in enumerate(
            df.groupby('IRS_halflife')):
        start = list(group_df['IRS_start'])
        data = list(group_df[dtype])
        error = list(group_df[dtype+'_std'])

        ax.set_xlabel('Start day')
        if 'averted' in dtype:
            ax.set_ylabel('Number of clinical cases averted', rotation=90)
        else:
            ax.set_ylabel('Prevalence reduction', rotation=90)
        ax.set_xlim([0, 365])
        ax.set_ylim(ylim)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=90)

        ind = iax
        if ref:
            color = 'k'
        else:
            color = intervention_colors[ind]
        if yerr:
            data = np.array(data)
            error = np.array(error)
            ax.plot(start, data, color=color, label=interventions[ind])
            ax.fill_between(start, data-error, data+error, color=color,
                            alpha=0.4)
        else:
            ax.plot(start, data, color=color, label=interventions[ind])
    if not ref:
        ax.legend(title='IRS half-life')


def plot_bars(fig, df, dtype, ylim=[], yerr=True, **kwargs):

        axes = fig.axes

        if not axes:
            fig.set_size_inches((15, 7))  # override smaller single-panel default from SiteDataPlotter
            axes = [fig.add_subplot(1, 1, 1)]

        intervention_colors = ['r', 'g', 'b', 'y', 'm', 'c', 'tab:orange', 'tab:purple',
                               'xkcd:sky blue', 'xkcd:neon purple', 'tab:brown', 'tab:gray', ]
        interventions = list(df['Intervention_type'].unique())
        width = 0.005
        offset = (len(interventions) - 1) * width/2
        offsets = list(np.linspace(-offset, offset, len(interventions)))
        ax = axes[0]
        lines = []
        intervention_labels = []

        for iax, (intervention, group_df) in enumerate(
                df.groupby('Intervention_type')):
            cov = list(group_df['Coverage'])
            data = list(group_df[dtype])
            error = list(group_df[dtype + '_std'])

            ax.set_xlabel('Coverage')
            if 'Annual_EIR' in dtype:
                ax.set_ylabel('Annual EIR reduction', rotation=90)
            else:
                ax.set_ylabel('Prevalence reduction', rotation=90)
            ax.set_xlim([0.5, 1.1])
            ax.set_ylim(ylim)
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=90)
            ax.set_xticks(list(set(cov)))

            for i in range(len(cov)):
                ind = iax
                if yerr:
                    line = ax.bar(cov[i] + offsets[ind], data[i], width=width, color=intervention_colors[ind],
                                  yerr=error[i], ecolor='k', align='center')
                else:
                    line = ax.bar(cov[i] + offsets[ind], data[i], width=width, color=intervention_colors[ind],
                                  ecolor='k', align='center')
            lines.append(line)
            intervention_labels.append(intervention)
            #
            # lines = lines[0:len(lines):len(cov)]
        return lines, intervention_labels


# Set up axes and call plot function
def plotting_coordinator(simmap, wdir, datadir, ftype):

    interventions = list(set(simmap['Intervention_type']))

    directory = datadir
    file = os.path.join(directory, 'Prevalence_EIR_across_runs_inset.csv')

    if not os.path.exists(file):
        data = get_data(simmap)
    else:
        data = pd.read_csv(file)

    if 'Unnamed: 0' in data.columns:
        data = data.drop('Unnamed: 0', axis=1)

        # BAR CHARTS - INFECTED

        # Prevalence reduction
        fig = plt.figure()

        ylim = [0.0, 1.0]

        lines, labels = plot_bars(fig, data, 'Infections_reduced', ylim=ylim, yerr=True)
        fig.legend(lines, labels, title='Interventions')

        fname = 'Prevalence_reduction_bars.' + ftype
        plt.suptitle('Prevalence reduction')
        plt.savefig(os.path.join(wdir, fname), format=ftype)
        plt.close('all')

        # Annual EIR
        fig = plt.figure()

        ylim = [0.0, np.max(data['Annual_EIR']) + np.max(data['Annual_EIR_std'])]

        lines, labels = plot_bars(fig, data, 'Annual_EIR', ylim=ylim, yerr=True)
        fig.legend(lines, labels, title='Interventions')

        fname = 'Annual_EIR_reduction_bars.' + ftype
        plt.suptitle('Annual_EIR_reduction')
        plt.savefig(os.path.join(wdir, fname), format=ftype)
        plt.close('all')


if __name__=='__main__':
    # exp_id = ['588df9a8-5b55-e811-a2bf-c4346bcb7274'] # Test
    # exp_id = ['adca88d9-945f-e811-a2bf-c4346bcb7274']  # Final - 15y
    exp_id = ['82e42ce5-cc68-e811-a2c0-c4346bcb7275']  # 10y
    exp_name = 'SMC_IV_uncor_10y'

    fig_dir = os.path.join('C:/Users/pselvaraj/Github/malaria-ml-mali/Figures', exp_name)
    if not os.path.exists((fig_dir)):
        os.mkdir(fig_dir)

    data_dir = os.path.join('C:/Users/pselvaraj/Github/malaria-ml-mali/Data', exp_name)
    if not os.path.exists((data_dir)):
        os.mkdir(data_dir)
    filepath_map = os.path.join(data_dir, 'Sim_map_inset.csv')

    if not os.path.exists(filepath_map):

        for exp in exp_id:
            temp_sim_map = make_simmap(exp, is_name=False, filetype='Inset')
            if 'sim_map' not in locals():
                sim_map = temp_sim_map
            else:
                sim_map = pd.concat([sim_map, temp_sim_map])
        sim_map.to_csv(os.path.join(data_dir, 'Sim_map_inset.csv'))

    else:

        sim_map = pd.read_csv(filepath_map)
    # sim_map = pd.read_csv(filepath_map)
    ftype = 'png'
    plotting_coordinator(sim_map, fig_dir, data_dir, ftype)
