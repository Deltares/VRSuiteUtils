import matplotlib.pyplot as plt
from matplotlib.pyplot import axis
import numpy as np

def plot_lcc_tc_from_steps(steps_dict: list[dict], axis: axis, lbl: str, clr: str, mrkr: str = 'o'):
    """Plot the total_lcc and total_risk from the optimization steps. It will give a 
    
    Args:
    steps_dict: list of dicts, each dict contains the optimization step number, data on total_lcc and total_risk
    axis: matplotlib axis object
    lbl: str, label for the plot
    clr: str, color for the plot
    mrkr: str, marker for the plot

    Returns:
    None

    """
    for count, step in enumerate(steps_dict):
        if count == 0:
            axis.plot(step['total_lcc'], step['total_risk'], label = lbl, color=clr, marker = mrkr, markersize=0.5)
        else:
            axis.plot(step['total_lcc'], step['total_risk'], color=clr, marker = mrkr, markersize=0.5)

def plot_traject_probability_for_step(traject_prob_step, ax, run_label = ''):
    def calculate_traject_probability(traject_prob):
        p_nonf = [1] * len(list(traject_prob.values())[0].values())
        for mechanism, data in traject_prob.items():
            time, pf = zip(*sorted(data.items()))
            p_nonf = np.multiply(p_nonf, np.subtract(1,pf))
        return time, list(1-p_nonf)
    time, pf_traject = calculate_traject_probability(traject_prob_step)
    ax.plot(time, pf_traject, label = run_label)

    # for mechanism, data in traject_prob_step.items():
    #     time, pf = zip(*sorted(data.items()))
    #     ax.plot(time, pf, label = f'{mechanism.name.capitalize()} {run_label}')
    ax.set_yscale('log')
    ax.set_xlabel('Time')
    ax.set_ylabel('Failure probability')
    ax.legend()