import numpy as np
import pandas as pd
import os
import json
import matplotlib.pyplot as plt
import matplotlib as mpl

from createSimDirectoryMapBR import createSimDirectoryMap

mpl.rcParams['pdf.fonttype'] = 42


# Make simmap from COMPS
def make_simmap(expname, is_name=True, filetype='Summary'):

    simmap = createSimDirectoryMap(expname)
    simmap = get_filepath(simmap, filetype)

    return simmap


# Get simmap for specific rows listed in restrictions
def get_simmap_restricted(simmap, restrictions={}):

    for restriction in restrictions:
        simmap = simmap.loc[simmap[restriction] == restrictions[restriction]]

    return simmap


# Get filelist of files in simmap
def get_filepath(simmap, filetype='Summary'):

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

    # Pull data from JSON file
    directory = data_dir
    if not os.path.exists(directory):
        os.makedirs(directory)
    file = os.path.join(directory, 'Cases_averted_raw_summary.csv')

    if not os.path.exists((file)):
        df = simmap.copy()
        listtodel = ['Serialized_Population_Path', 'exe_collection_id', 'dll_collection_id', 'input_collection_id', 'outpath', 'simid',
                     'add_summary_report.start_day']
        if 'Unnamed: 0' in df.columns:
            df = df.drop('Unnamed: 0', axis=1)
        df = df.drop(listtodel, axis=1)
        df['Cases_averted'] = [[None]*3] * len(df['filelist'])

        for file in df['filelist']:
            with open(file) as fin:
                datatemp = json.loads(fin.read())
                # Sum of all cases for second year
                incidence = datatemp['DataByTimeAndAgeBins']['Annual Clinical Incidence by Age Bin']
                population = datatemp['DataByTimeAndAgeBins']['Average Population by Age Bin']
                clinical_cases = np.array([np.array([incidence[i][j]*population[i][j]/365 for j in range(3)])
                                           for i in range(len(population))])
                clinical_cases = list(np.sum(clinical_cases, axis=0))
                mask = df['Cases_averted'].loc[df['filelist'] == file].index[0]
                df['Cases_averted'][mask] = clinical_cases

        temp_data = get_no_intervention_data()
        df = df.sort_values(df.columns.tolist()[:-1])

        for (group, group_df) in df.groupby(['Intervention_type'], as_index=False):
            ref_clinical = np.array(eval(temp_data['New_clinical_cases'].values[0]))
            mask = list(group_df.index)
            templist = list(group_df['Cases_averted'].apply(lambda x: list(ref_clinical-np.array(x))))
            df['Cases_averted'][mask] = templist

        df = df.drop('filelist', axis=1)
        directory = data_dir
        if not os.path.exists(directory):
            os.makedirs(directory)
        file = os.path.join(directory, 'Cases_averted_raw_summary.csv' )
        df.to_csv(file)

    else:
        df = pd.read_csv(file)

    if 'Unnamed: 0' in df.columns:
        df = df.drop('Unnamed: 0', axis=1)
    listtoavg = [e for e in list(df.columns.values) if e not in ('Run_Number', 'Cases_averted')]
    df['Cases_averted_np'] = df['Cases_averted'].apply(lambda x: np.array(eval(x)))
    # df1 = df.groupby(listtoavg)['Cases_averted'].mean().reset_index()
    df1 = pd.DataFrame(df.groupby(listtoavg, as_index=False)['Cases_averted_np'].apply(np.mean)).reset_index()
    df1['Cases_averted_std'] = [[None] * 3] * len(df1['Cases_averted_np'])
    df1 = df1.rename(columns = {'Cases_averted_np':'Cases_averted'})
    for (group, group_df) in df.groupby(listtoavg, as_index=False):
        temparray = list(np.std(np.array(list(group_df['Cases_averted_np'])), axis=0))
        temparraymean = list(np.mean(np.array(list(group_df['Cases_averted_np'])), axis=0))
        mask = df1.loc[(df1['Start'] == group[-1]) & (df1['Intervention_type'] == group[1]) & (df1['Coverage'] == group[0])].index[0]
        df1['Cases_averted_std'][mask] = temparray
        df1['Cases_averted'][mask] = temparraymean

    file = os.path.join(directory, 'Cases_averted_across_runs_summary.csv')
    df1.to_csv(file)

    return df1


def get_ref_data(simmap):

    df = simmap.copy()
    listtodel = ['Serialized_Population_Path', 'exe_collection_id', 'dll_collection_id', 'input_collection_id', 'outpath', 'simid',
                 'add_summary_report.start_day']
    df = df.drop(listtodel, axis=1)
    df['New_clinical_cases'] = [[None]*3] * len(df['filelist'])

    directory = data_dir
    if not os.path.exists(directory):
        os.makedirs(directory)
    filesummary = os.path.join(directory, 'Reference_raw_summary.csv')

    if os.path.exists(filesummary):
        df = pd.read_csv(filesummary)
    else:
        for file in df['filelist']:
            with open(file) as fin:
                datatemp = json.loads(fin.read())
                # Sum of all cases for second year
                incidence = datatemp['DataByTimeAndAgeBins']['Annual Clinical Incidence by Age Bin']
                population = datatemp['DataByTimeAndAgeBins']['Average Population by Age Bin']
                clinical_cases = np.array([np.array([incidence[i][j] * population[i][j] / 365 for j in range(3)]) for i in
                                           range(len(population))])
                clinical_cases = list(np.sum(clinical_cases, axis=0))
                mask = df['New_clinical_cases'].loc[df['filelist'] == file].index[0]
                df['New_clinical_cases'][mask] = clinical_cases

        df.to_csv(filesummary)

    if 'Unnamed: 0' in df.columns:
        df = df.drop('Unnamed: 0', axis=1)

    df = df.drop('filelist', axis=1)
    listtoavg = [e for e in list(df.columns.values) if e not in ('Run_Number', 'New_clinical_cases')]
    df1 = pd.DataFrame(df['Simulation_Duration'].unique(), columns=['Simulation_Duration'])
    df1['New_clinical_cases'] = [[None] * 3] * len(df1['Simulation_Duration'])
    for iax, (group, group_df) in enumerate(df.groupby(listtoavg, as_index=False)):
        templist = group_df['New_clinical_cases'].tolist()
        templist = list(np.mean(np.array([np.array(list1) for list1 in templist]), axis=0))
        mask = df1['Simulation_Duration'].loc[df1['Simulation_Duration'] == group].index[0]
        df1['New_clinical_cases'][mask] = templist

    file = os.path.join(directory, 'Reference_averaged_across_runs_summary.csv')
    df1.to_csv(file)

    return df1


def get_no_intervention_data():

    directory = data_dir
    # exp = '2ab297ab-5961-e811-a2c0-c4346bcb7275' # No intervention - 15y
    exp = 'f8091726-c968-e811-a2c0-c4346bcb7275' # No intervention - 10y
    sim_map = make_simmap(exp, is_name=False, filetype='Summary')

    if not os.path.exists((directory)):
        os.mkdir(directory)
    # filepath_map = os.path.join(directory, 'Sim_map_reference_summary.csv')
    sim_map.to_csv(os.path.join(data_dir, 'Sim_map_reference_summary.csv'))

    file = os.path.join(directory, 'Reference_averaged_across_runs_summary.csv')
    if not os.path.exists(file):
        data = get_ref_data(sim_map)
    else:
        data = pd.read_csv(file)

    return data


def plot_lines_with_shaded_areas(fig, df, dtype, ref=False, ylim=[], yerr=True, **kwargs):

    axes = fig.axes
    ages = [5, 10, 100]

    if not axes:
        fig.set_size_inches((15, 7))  # override smaller single-panel default from SiteDataPlotter
        axes = [fig.add_subplot(1, 1, 1)]

    intervention_colors = ['r', 'g', 'b', 'y', 'm']
    coverages = list(df['Coverage'].unique())

    ax = axes[0]

    for iax, (intervention, group_df) in enumerate(
            df.groupby('Intervention_type')):
        data = list(group_df[dtype])
        error = list(group_df[dtype+'_std'])
        data = np.array([np.array(eval(x)) for x in data])
        error = np.array([np.array(eval(x)) for x in error])

        ax.set_xlabel('Coverage')
        if 'averted' in dtype:
            ax.set_ylabel('Number of clinical cases averted', rotation=90)
        else:
            ax.set_ylabel('Prevalence reduction', rotation=90)
        ax.set_xlim([0.6, 1.0])
        ax.set_ylim(ylim)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=90)

        ind = iax
        if ref:
            color = 'k'
        else:
            color = intervention_colors[ind]
        for i in range(data.shape[1]):
            age = '<' + str(ages[i])
            ax.plot(coverages, data[:, i], color=color, label=age, alpha=(i+1)/3.0)
            ax.fill_between(coverages, data[:, i] - error[:, i], data[:, i] + error[:, i], color=color,
                        alpha=0.4*(i+1)/3.0)
    if not ref:
        ax.legend(title='Age')


def plot_bars(fig, df, dtype, age_bin_index, ylim=[], yerr=True, **kwargs):

    axes = fig.axes

    if not axes:
        fig.set_size_inches((15, 7))  # override smaller single-panel default from SiteDataPlotter
        axes = [fig.add_subplot(1, 1, 1)]

    intervention_colors = ['r', 'g', 'b', 'y', 'm', 'c', 'tab:orange', 'tab:purple',
                           'tab:brown', 'tab:gray', 'xkcd:sky blue', 'xkcd:neon purple']
    interventions = list(df['Intervention_type'].unique())
    width = 0.005
    offset = (len(interventions) - 1) * width / 2
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
        if 'Cases_averted' in dtype:
            ax.set_ylabel('Clinical cases averted', rotation=90)
        ax.set_xlim([0.5, 1.1])
        ax.set_ylim(ylim)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=90)
        ax.set_xticks(list(set(cov)))

        for i in range(len(cov)):
            ind = iax
            if yerr:
                line = ax.bar(cov[i] + offsets[ind], eval(data[i])[age_bin_index], width=width, color=intervention_colors[ind],
                              yerr=eval(error[i])[age_bin_index], ecolor='k', align='center')
            else:
                line = ax.bar(cov[i] + offsets[ind], eval(data[i])[age_bin_index], width=width, color=intervention_colors[ind],
                              ecolor='k', align='center')
        lines.append(line)
        intervention_labels.append(intervention)
        #
        # lines = lines[0:len(lines):len(cov)]
    return lines, intervention_labels


# Set up axes and call plot function
def plotting_coordinator(simmap, wdir, datadir, ftype):

    directory = datadir
    file = os.path.join(directory, 'Cases_averted_across_runs_summary.csv')

    if not os.path.exists(file):
        data = get_data(simmap)
    else:
        data = pd.read_csv(file)

    if 'Unnamed: 0' in data.columns:
        data = data.drop('Unnamed: 0', axis=1)

    age_bins = [5, 15, 100]

    for i, age in enumerate(age_bins):

        age_data = [eval(a)[i] for a in list(data['Cases_averted'])]
        age_data_std = [eval(a)[i] for a in list(data['Cases_averted_std'])]
        ylim = [0, np.max(age_data) + np.max(age_data_std)]

        fig = plt.figure()

        lines, labels = plot_bars(fig, data, 'Cases_averted', age_bin_index=i, ylim=ylim)
        fig.legend(lines, labels, title='Interventions')

        fname = 'Cases_averted_age%i_' % age + '.' + ftype
        plt.suptitle('Cases Averted')
        plt.savefig(os.path.join(wdir, fname), format=ftype)
        plt.close('all')

    # for i in interventions:
    #     df = data.loc[data['Intervention_type'] == i]
    #
    #     fig = plt.figure()
    #
    #     # ylim = [0.0, max(data['Cases_averted']) + 0.1 * max(data['Cases_averted'])]
    #     ylim = [0, 500]
    #
    #     plot_lines_with_shaded_areas(fig, df, 'Cases_averted', ylim=ylim)
    #
    #     fname = 'Cases_averted_%s_' %i + '.' + ftype
    #     plt.suptitle('Cases Averted')
    #     plt.savefig(os.path.join(wdir, fname), format=ftype)
    #     plt.close('all')


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
    filepath_map = os.path.join(data_dir, 'Sim_map_summary.csv')

    if not os.path.exists(filepath_map):

        for exp in exp_id:
            temp_sim_map = make_simmap(exp, is_name=False, filetype='Summary')
            if 'sim_map' not in locals():
                sim_map = temp_sim_map
            else:
                sim_map = pd.concat([sim_map, temp_sim_map])
        sim_map.to_csv(os.path.join(data_dir, 'Sim_map_summary.csv'))

    else:

        sim_map = pd.read_csv(filepath_map)

    ftype = 'png'
    plotting_coordinator(sim_map, fig_dir, data_dir, ftype)
