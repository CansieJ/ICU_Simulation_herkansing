import argparse
from lib.model import ICUModel
import os
import json
import solara

with open('./batch_run_config.json') as file:
    params = json.load(file)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Process a time parameter.")
    
    # Adding the --time argument
    parser.add_argument(
        "--time",
        type=int,
        required=True,
        help="Specify the time in days, e.g: 3."
    )

    args = parser.parse_args()
    time = args.time

    if not os.path.exists("./runs"):
        os.mkdir("./runs")

    current_index = len(os.listdir("./runs"))
    os.mkdir(f"./runs/run{current_index}")
    run_datas = []
    for i in range(len(params)):
        os.mkdir(f"./runs/run{current_index}/params{i}")
        opnames_file = f"./runs/run{current_index}/params{i}/opnames.csv"
        refused_file = f"./runs/run{current_index}/params{i}/geweigerd.csv"
        costs_file = f"./runs/run{current_index}/params{i}/costs.csv"
        capacity_file = f"./runs/run{current_index}/params{i}/capacity.csv"
        amount_file = f"./runs/run{current_index}/params{i}/amount.csv"
        replanning_file = f"./runs/run{current_index}/params{i}/replanning.csv"
        model = ICUModel(amount=params[i]["amount"], 
                         clock_speed=params[i]["clock_speed"], 
                         departments=solara.reactive(params[i]["departments"]), 
                         distribution=solara.reactive(params[i]["distribution"]), 
                         planning_method=params[i]["planning_method"],
                         capacity=params[i]["capacity"],
                         use_ic_spike=params[i]["use_ic_spike"]
                         )
       
        for j in range(int((60*24*time)/params[i]["clock_speed"])):
            model.step()

        model.datacollector.get_table_dataframe("admissions").to_csv(opnames_file, sep=";")
        model.datacollector.get_table_dataframe("refused").to_csv(refused_file, sep=";")
        model.datacollector.get_table_dataframe("costs").to_csv(costs_file, sep=";")
        model.datacollector.get_table_dataframe("capacity").to_csv(capacity_file, sep=";")
        model.datacollector.get_table_dataframe("amount").to_csv(amount_file, sep=";")
        model.datacollector.get_table_dataframe("replanning").to_csv(replanning_file, sep=";")
