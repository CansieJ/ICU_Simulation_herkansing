import solara
import numpy as np

@solara.component
def NestedMultiSelect(model):
    assignments, set_assignments = solara.use_state(model.departments.value)
    options = ["CAPU", "CARD", "INT", "Other", "CHIR", "NEC", "NEU"]
    real_options = list(set(options) - set(np.concatenate(model.departments.value)))
    def add_group():
        global real_options
        updated_assignments = assignments[:]
        updated_assignments.append([])  # Add a new empty group
        set_assignments(updated_assignments)
        model.departments.value = updated_assignments  # Update the model parameter
        real_options = list(set(options) - set(np.concatenate(model.departments.value)))

    def remove_group(index):
        global real_options
        updated_assignments = assignments[:]
        if len(updated_assignments) > 1:  # Ensure at least one group remains
            del updated_assignments[index]
            set_assignments(updated_assignments)
            model.departments.value = updated_assignments 
            
            real_options = list(set(options) - set(np.concatenate(model.departments.value)))

    def update_group(index, values):
        global real_options
        updated_assignments = assignments[:]
        updated_assignments[index] = values
        set_assignments(updated_assignments)
        model.departments.value = updated_assignments
        
        real_options = list(set(options) - set(np.concatenate(model.departments.value)))
    
    with solara.Column():
        solara.Markdown("### Help")
        for i, group in enumerate(assignments):
            with solara.Row():
                solara.Markdown(f"**Group {i + 1}:**")
                solara.Button(
                    label="Remove Group",
                    on_click=lambda i=i: remove_group(i),
                    color="red",
                    outlined=True,
                    dense=True,
                )
            solara.SelectMultiple(
                label=f"Select items for Group {i + 1}",
                all_values=real_options + group,
                values=group,
                on_value=lambda values, i=i: update_group(i, values),
            )
        solara.Button(label="Add Group", on_click=add_group, color="green")
        solara.Markdown("### Current Assignments")
        solara.Markdown(f"```\n{assignments}\n```")
            # solara.Markdown(f"**Group {i + 1}:")
            # solara.SelectMultiple(label=f"Select items for group {i + 1}", all_values=options, values=group, on_value=lambda values, i=i: update_group(i, values))
            # solara.Markdown("### pleH")
            # solara.Markdown(f"```json\n{assignments}\n```")

model_parameters = {
    "seed": {
        "type": "SliderInt",
        "value": 1,
        "label": "Seed",
        "min": 10,
        "max": 2**32-1,
    },
    "size": {
        "type": "SliderInt",
        "value": 20,
        "label": "Grid Size",
        "min": 0,
        "max": 50,
        "step": 10,
    },
    "amount": {
        "type": "SliderInt",
        "value": 2200,
        "label": "Amount of yearly patients",
        "min": 1000,
        "max": 10000,
        "step": 100
    },
    "clock_speed": {
        "type": "SliderInt",
        "values": 10,
        "label": "Clock speed (minutes per step)",
        "min": 1,
        "max": 15,
        "step": 1
    },
    "planning_method": {
        "type": "SliderInt",
        "value": 1,
        "label": "Replanner method",
        "min": 1,
        "max": 3,
        "step": 1
    },
    "capacity": {
        "type": "SliderInt",
        "value": 32,
        "label": "Total ICU capacity",
        "min": 1,
        "max": 100,
        "step": 1
    },
    "efficiency": {
        "type": "SliderInt",
        "value": 0,
        "label": "Efficiency Percentage",
        "min": 0,
        "max": 25,
        "step": 1
    },
    "pandemic_allocation_percentage": {
        "type": "SliderInt",
        "value": 0,
        "label": "Pandemic Allocation Percentage",
        "min": 0,
        "max": 50,
        "step": 1
    },
    "use_ic_spike":  {
        "type": "Checkbox",
        "value": False,
        "label": "Use IC Spike"
    }
}