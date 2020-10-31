# Created by William Edwards (wre2@illinois.edu)

# Standard project includes
import sys
from pdb import set_trace
import matplotlib

# External project includes
import numpy as np
import matplotlib.pyplot as plt

# Internal project includes
from utils import *

def make_figure_sysid1():
    models = [("ARX", "arx"), ("Koopman", "koop"),
            ("SINDy", "sindy"), ("MLP", "mlp")]
    tasks = [("Pendulum swing-up", "pendulum-swingup"),
            ( "Cartpole swing-up", "cartpole-swingup")]
    settings = [
            ["cartpole-swingup", "arx", 10, 42],
            ["cartpole-swingup", "mlp", 100, 42],
            ["cartpole-swingup", "koop", 40, 42],
            ["cartpole-swingup", "sindy", 100, 42],
            ["cartpole-swingup", "approxgp", 100, 42],
            ["pendulum-swingup", "arx", 10, 42],
            ["pendulum-swingup", "mlp", 100, 42],
            ["pendulum-swingup", "koop", 40, 42],
            ["pendulum-swingup", "sindy", 100, 42],
            ["pendulum-swingup", "approxgp", 100, 42]]
    print("SysID Figure")
    print("============")
    print("SystemID ", end="")
    for task_label, _ in tasks:
        print(" & " + task_label, end="") 
    print(r"\\")
    for model_label, model_id in models:
        print(f"{model_label:8} ", end="")
        for task_label, task_id in tasks:
            for setting in settings:
                if setting[0] == task_id and setting[1] == model_id:
                    if result_exists("sysid1", *setting):
                        final_score, _ = load_result("sysid1", *setting)
                        print(f"& {final_score:8.2f} ", end="")
                        break
            else:
                print("&          ", end="")
        print(r" \\")

def make_figure_cost_tuning():
    setting = ("cartpole-swingup", "mlp-ilqr", 100, 42)
    result, baseline_res = load_result("cost_tuning", *setting)

    matplotlib.rcParams.update({'font.size': 12})
    fig = plt.figure(figsize=(4,4))
    ax = fig.gca()
    ax.set_title(f"Cost Tuning Performance")
    ax.set_xlabel("Tuning iterations")
    ax.set_ylabel("True Perf.")
    perfs = [cost for cost in result["inc_truedyn_costs"]]
    print(f"{perfs=}")
    ax.plot(perfs)
    ax.plot([0.0, len(perfs)], [baseline_res[1], baseline_res[1]], "k--")
    ax.legend(["Tuned Quad. Cost", "Untuned Perf. Metric"])
    plt.tight_layout()
    plt.show()

def make_figure_tuning1():
    #experiments = [
    #        (("MLP-iLQR", "Pendulum"),
    #         ("pendulum-swingup", "mlp-ilqr", 100, 42)),
    #        (("MLP-iLQR", "Cartpole"),
    #         ("cartpole-swingup", "mlp-ilqr", 100, 42)),
    #        (("MLP-iLQR", "Acrobot"),
    #            ("acrobot-swingup", "mlp-ilqr", 100, 42))
    #        ]
    experiments = [
            (("MLP-iLQR", "Half-Cheetah"),
             ("halfcheetah", "mlp-ilqr", 100, 42)),
            ]
    #bcq_baselines = [24, 37, 1000]
    bcq_baselines = [-1000]
    for i, ((pipeline_label, task_label), setting) in enumerate(experiments):
        #if not result_exists("tuning1", *setting):
        #    print(f"Skipping {pipeline_label}, {task_label}")
        #    continue
        #result = load_result("tuning1", *setting)

        matplotlib.rcParams.update({'font.size': 12})
        fig = plt.figure(figsize=(4,4))
        ax = fig.gca()
        ax.set_title(f"{pipeline_label} on {task_label}")
        ax.set_xlabel("Tuning iterations")
        ax.set_ylabel("True Perf.")
        #labels = []
        #for label, value in baselines:
        #    ax.plot([0.0, n_iters], [value, value], "--")
        #    labels.append(label)
        #for label, res in tuning_results:
        #    perfs = [-cost for cost in res["inc_truedyn_costs"]]
        #    ax.plot(perfs)
        #    labels.append(label)
        #ax.legend(labels)
        #perfs = [cost for cost in result["inc_costs"]]
        perfs = [263.0] * 6 + [113.0]*4 + [535]*7 + [29]*25
        print(f"{perfs=}")
        ax.plot(perfs)
        ax.plot([0, len(perfs)], [bcq_baselines[i], bcq_baselines[i]], "r--") 
        ax.legend(["Ours", "BCQ Baseline"])
        plt.tight_layout()
        plt.show()

def make_figure_decoupled1():
    result = load_result("decoupled1", "cartpole-swingup", "mlp-ilqr", 100,
            42)

    matplotlib.rcParams.update({'font.size': 12})
    fig = plt.figure(figsize=(4,4))
    ax = fig.gca()
    ax.set_title(f"MLP-iLQR on Half-cheetah")
    ax.set_xlabel("Tuning iterations")
    ax.set_ylabel("True Perf.")
    #labels = []
    #for label, value in baselines:
    #    ax.plot([0.0, n_iters], [value, value], "--")
    #    labels.append(label)
    #for label, res in tuning_results:
    #    perfs = [-cost for cost in res["inc_truedyn_costs"]]
    #    ax.plot(perfs)
    #    labels.append(label)
    #ax.legend(labels)
    #perfs = [cost for cost in result["inc_costs"]]
    perfs = [263.0] * 6 + [113.0]*4 + [535]*7 + [29]*25
    print(f"{perfs=}")
    ax.plot(perfs)
    ax.plot([0, len(perfs)], [37, 37], "r--") 
    ax.legend(["Decoupled tune", "BCQ Baseline"])
    plt.tight_layout()
    plt.show()

def make_figure_sysid2():
    setting1 = ("cartpole-swingup", "mlp-ilqr", 1, 100, 42)
    setting2 = ("cartpole-swingup", "mlp-ilqr", 2, 100, 42)
    setting3 = ("cartpole-swingup", "mlp-ilqr", 3, 100, 42)

    smac_res1, (rmses1, horizs1) = load_result("sysid2", *setting1)
    smac_res2, (rmses2, horizs2) = load_result("sysid2", *setting2)
    smac_res3, (rmses3, horizs3) = load_result("sysid2", *setting3)

    set_trace()

    matplotlib.rcParams.update({'font.size': 12})
    fig = plt.figure(figsize=(4,4))
    ax = fig.gca()
    ax.set_xlabel("Prediction Horizon")
    ax.set_ylabel("RMSE")
    ax.set_title("Multi-Step Pred. Accuracy")
    ax.plot(horizs1, rmses1)
    ax.plot(horizs2, rmses2)
    ax.plot(horizs3, rmses3)
    ax.legend(["1-step train", "Multi-step train", "Pipeline train"])

    #fig = plt.figure(figsize=(4,4))
    #ax = fig.gca()
    #ax.set_xlabel("Tuning Iterations")
    #ax.set_ylabel("Performance")
    #ax.set_title("Pipeline Performance of Sys ID")
    #ax.plot(smac_res1["inc_truedyn_costs"])
    #ax.plot(smac_res2["inc_truedyn_costs"])
    #ax.plot(smac_res3["inc_truedyn_costs"])
    #ax.legend(["1-step train", "Multi-step train", "Pipeline train"])

    plt.tight_layout()
    plt.show()


def main(command):
    if command == "sysid1":
        make_figure_sysid1()
    elif command == "tuning1":
        make_figure_tuning1()
    elif command == "sysid2":
        make_figure_sysid2()
    elif command == "cost_tuning":
        make_figure_cost_tuning()
    elif command == "decoupled":
        make_figure_decoupled1()
    else:
        raise Exception("Unrecognized command")

if __name__ == "__main__":
    main(sys.argv[1])
