#!/usr/bin/env python3

import datetime
from madsci.common.types.workflow_types import WorkflowDefinition
from madsci.common.types.step_types import StepDefinition
from madsci.client.experiment_application import ExperimentApplication
from pathlib import Path

from helper_functions.hso_functions import package_hso
from protocols import solo_transfer1

console = Console()


class DemoAMPExperimentApplication(ExperimentApplication): 
    """Experiment application for the AMP Demo"""

    workflow_directory = Path("./workflows").resolve()
    protocol_directory = Path("./protocols").resolve()

    # Q: How does it know which workcell to run on? 
    url = "http://hudson01:8000"  # ???


    def run_demo(self): 

        # workflow path(s)
        demo_wf = self.workflow_directory / "demo_wf.yaml"

        # initial payload
        parameters = {
            "temp": 37.0, #a float value setting the temperature of the Liconic Incubator (in Celsius) 
            "humidity": 95.0, # a float value setting the humidity of the Liconic Incubator
            "shaker_speed": 30, #an integer value setting the shaker speed of the Liconic Incubator
            "stacker": 1, # an integer value specifying which stacker a well plate should be used in (Preferable to use "incubation_plate_id" : plate_id, where plate_id is an integer 1-88 - stacker and slot will be autocalculated)
            "slot": 2, # an integer value specifying which slot a well plate should be used in (Preferable to use "incubation_plate_id" : plate_id, where plate_id is an integer 1-88 - stacker and slot will be autocalculated)
            "tip_box_position": "3", # string of an integer 1-8 that identifies the position of the tip box when it is being refilled
        }

        # generate and format SOLO hso protocol, then add to parameters dict
        hso_1, hso_1_lines, hso_1_basename = package_hso(
            solo_transfer1.generate_hso_file, parameters, "/home/rpl/wei_temp/solo_temp1.hso"
        )
        parameters["hso_1"] = hso_1
        parameters["hso_1_lines"] = hso_1_lines
        parameters["hso_1_basename"] = hso_1_basename

        # run the demo workflow
        self.workcell_client.submit_workflow(
            workflow = self.demo_wf, 
            parameters=parameters
        )


if __name__ == "__main__":

    experiment_app = DemoAMPExperimentApplication()

    current_time = datetime.datetime.now()

    with experiment_app.manage_experiment(
        run_name=f"Demo AMP Experiment Run {current_time}",
        run_description=f"Run for demo AMP experiment, started at ~{current_time}",
    ):

        experiment_app.run_demo()