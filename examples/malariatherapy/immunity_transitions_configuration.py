import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import copy


def probability_shifting_module(TM, immune_stimulation_threshold,row_scale_factor,column_scale_factor):
    number_of_bin_edges = max([len(i) for i in TM])
    bin_numbers = np.arange(0, number_of_bin_edges)
    new_TM = copy.copy(TM)
    rows_to_cycle_through = np.arange(immune_stimulation_threshold, max(bin_numbers) + 1)
    # define a row scaling factor that represents the changing force of immunity across current density classes
    for row in rows_to_cycle_through:
        Old_column_values = [x for x in TM[row]]
        Bin_decreases = [np.log10(column_scale_factor * row_scale_factor * bin) for bin in bin_numbers]
        New_column_values = [Old_column_values[i] / Bin_decreases[i] for i in range(len(Old_column_values))]

        Net_zero_column_change = sum(
            [abs(New_column_values[j] - Old_column_values[j]) for j in np.arange(1, len(Old_column_values))])
        New_column_values[0] = Old_column_values[0] + Net_zero_column_change
        new_TM[row] = New_column_values

    return(TM,new_TM)

def set_transition_matrix(cb,TM,scale_factor,immune_stim_threshold = 1):
    old_TM, shifted_TM = probability_shifting_module(TM,immune_stim_threshold, row_scale_factor= scale_factor,column_scale_factor= scale_factor)
    cb.update_params({"Parasite_Peak_Density_Probabilities": shifted_TM,
                      ".Scale_Factor": scale_factor})

    return {"scale_factor": scale_factor}

def plot_heatmap_transition_changes(old_TM, new_TM):
    diffs =pd.DataFrame(np.zeros((len(old_TM), len(old_TM))))

    cmap =  'coolwarm'

    for row in range(len(old_TM)):
        for col in range(len(old_TM)):
            diffs[row][col] = old_TM[row][col] - new_TM[row][col]

    plt.imshow(diffs,cmap = cmap,vmin = -1, vmax = 1)
    plt.show()

if __name__ == '__main__':
    TM = [
        [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.373134328, 0.0, 0.358208955, 0.179104478, 0.074626866, 0.014925373, 0.0],
        [0.277108434, 0.0, 0.289156627, 0.301204819, 0.132530120, 0.0, 0.0],
        [0.042253521, 0.0, 0.126760563, 0.232394366, 0.542253521, 0.056338028, 0.0],
        [0.168421053, 0.0, 0.010526316, 0.126315789, 0.410526316, 0.284210526, 0.0],
        [0.176470588, 0.0, 0.058823529, 0.0, 0.235294118, 0.529411765, 0.0]
    ]
    TMpd = pd.DataFrame(TM)
    # What rows am I going to go about scaling? (Reminder... Row 0 transitions from truezero, and Row 6 is from highest density)
    immune_stim_threshold = 6
    # whats the base parameter I want to use to describe how immunity impacts these different density classes?
    row_scale_factor = 1
    # whats the base parameter I want to use to describe how immunity impacts the transitions within a density class?
    column_scale_factor = 1

    plt.imshow(-TMpd.T, cmap='coolwarm', vmin=-1, vmax=1)
    plt.show()
    def test_transition_matrix(scale_factor):
        old_TM, shifted_TM = probability_shifting_module(TM, 1, row_scale_factor=scale_factor,
                                                         column_scale_factor=scale_factor)

        plot_heatmap_transition_changes(old_TM, shifted_TM)

        return (old_TM, shifted_TM)
    for scale_num in [2,5,10,100]:
        old_TM, shifted_TM = test_transition_matrix(scale_num)