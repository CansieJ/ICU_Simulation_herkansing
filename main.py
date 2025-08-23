from mesa.visualization import (
    SolaraViz,
    make_space_component,
    make_plot_component
)
from solara import reactive
from lib.agents import Patient, Frontdesk, Department, Home
from lib.params import model_parameters, NestedMultiSelect
from lib.utils import get_color
from lib.model import ICUModel

def agent_portrayal(agent: Patient) ->  None:
    if (agent is None):
        return
    
    portrayal = {
        "size": 50,
        "color": (0, 0, 0)
    }
    
    if(isinstance(agent, Patient)):
        portrayal["color"] = (0, 1, 0) if agent.planned else (1,0 ,0) #get_color(agent.sickness)
        portrayal["marker"] = "s"
        portrayal["label"] = "Patient"
    elif(isinstance(agent, Frontdesk)):
        portrayal["color"] = (0, 0, 0)
        portrayal["label"] = "Patient"
    elif(isinstance(agent, Department)):
        portrayal["color"] = (0, 0, 1)   
        portrayal["label"] = "Patient"
    elif(isinstance(agent, Home)):
        portrayal["color"] = (0.5, 0.5, 0.5)   
        portrayal["label"] = "Home"
        portrayal["marker"] = "^"
        portrayal["zorder"] = 10

    return portrayal

def post_process (ax) -> None:
    ax.set_aspect(0.75)
    ax.figure.set_size_inches(8, 8) 
    ax.set_xticks([])
    ax.set_yticks([])
    # ax.legend(loc="center left", bbox_to_anchor=(1, 0.9))
    m = model.value
    ax.text(0.05, 0.95, f'Time: {m.clock.get_time()}', transform=ax.transAxes,
            fontsize=14, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.5))

model = reactive(ICUModel())


GridGraph = make_space_component(agent_portrayal, backend="matplotlib", post_process=post_process)

PlotGraph = make_plot_component("Capacity")
# CostsGraph = make_plot_component("Costs")

page = SolaraViz(
    model=model,
    model_params=model_parameters,
    components=[GridGraph, PlotGraph, NestedMultiSelect],
    name="ICU Simulation",
    play_interval=0
)

page