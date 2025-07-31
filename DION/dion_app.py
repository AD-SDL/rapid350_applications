#!/usr/bin/env python3

import datetime
from madsci.common.types.workflow_types import WorkflowDefinition
from madsci.common.types.step_types import StepDefinition
from madsci.client.experiment_application import ExperimentApplication
from pathlib import Path

from helper_functions.hso_functions import package_hso
from protocols import dispense_DMSO, dispense_control_and_test, serial_dilute_test_compound

class DionExperimentApplication(ExperimentApplication):
    """Experiment application for Dion's LDRD experiment"""

    workflow_directory = Path("./workflows").resolve()
    protocol_directory = Path("./protocols").resolve()
    experiment_design = Path("./experiment_design.yaml")

    url = "http://hudson01:8000"


    def run_app(self):

        # workflow path(s)
        run_solo_wf = self.workflow_directory / "run_solo.yaml"

        # initial payload
        parameters = {
            "temp": 37.0, #a float value setting the temperature of the Liconic Incubator (in Celsius)
            "humidity": 95.0, # a float value setting the humidity of the Liconic Incubator
            "shaker_speed": 30, #an integer value setting the shaker speed of the Liconic Incubator
            "stacker": 1, # an integer value specifying which stacker a well plate should be used in (Preferable to use "incubation_plate_id" : plate_id, where plate_id is an integer 1-88 - stacker and slot will be autocalculated)
            "slot": 2, # an integer value specifying which slot a well plate should be used in (Preferable to use "incubation_plate_id" : plate_id, where plate_id is an integer 1-88 - stacker and slot will be autocalculated)
            "tip_box_position": "5", # string of an integer 1-8 that identifies the position of the tip box when it is being refilled
            "seal_time": 3, # an integer value setting the time in seconds for the sealer to seal a plate
        }

        # generate SOLO protocol: dispense DMSO into dilution column wells
        hso_1, hso_1_lines, hso_1_basename = package_hso(
            dispense_DMSO.generate_hso_file, parameters, "/home/rpl/wei_temp/solo_temp1.hso"
        )
        parameters["protocol_file"] = "/home/rpl/wei_temp/solo_temp1.hso"

        # run SOLO protocol: dispense DMSO into dilution column wells   # WORKING
        self.workcell_client.submit_workflow(
            workflow = run_solo_wf,
            parameters=parameters
        )

        # generate SOLO protocol: dispense control and test compounds
        hso_2, hso_2_lines, hso_2_basename = package_hso(
            dispense_control_and_test.generate_hso_file, parameters, "/home/rpl/wei_temp/solo_temp2.hso"
        )
        parameters["protocol_file"] = "/home/rpl/wei_temp/solo_temp2.hso"

        # run SOLO protocol: dispense control and test compounds   # NOT TESTED
        self.workcell_client.submit_workflow(
            workflow = run_solo_wf,
            parameters=parameters
        )

        # generate SOLO protocol: serial dilute test compound
        hso_3, hso_3_lines, hso_3_basename = package_hso(
            serial_dilute_test_compound.generate_hso_file, parameters, "/home/rpl/wei_temp/solo_temp3.hso"
        )
        parameters["protocol_file"] = "/home/rpl/wei_temp/solo_temp3.hso"

        # run SOLO protocol: serial dilute test compound   # NOT TESTED
        self.workcell_client.submit_workflow(
            workflow = run_solo_wf,
            parameters=parameters
        )






if __name__ == "__main__":

    experiment_app = DionExperimentApplication()

    current_time = datetime.datetime.now()

    with experiment_app.manage_experiment(
        run_name=f"Dion's Experiment Run {current_time}",
        run_description=f"Run for Dion's LDRD experiment, started at ~{current_time}",
    ):

        experiment_app.run_app()