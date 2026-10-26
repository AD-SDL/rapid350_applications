"""
Main MADSci Experiment Application for the AMES Test LDRD Project at Argonne National Laboratory.
"""

import datetime
import time
from pathlib import Path

from helper_functions.hso_functions import package_hso
from madsci.common.types.step_types import StepDefinition
from madsci.common.types.workflow_types import WorkflowDefinition
from madsci.experiment_application import (
    ExperimentApplication,
    ExperimentApplicationConfig,
)
from madsci.common.types.resource_types import Slot, Stack, Resource, Collection, Grid

from madsci.client import (
    ExperimentClient,
    LocationClient,
    ResourceClient,
    WorkcellClient,
)
from protocols import (
    dispense_cells_then_compound,
    dispense_control_and_test,
    dispense_DMSO,
    dispense_into_384_plate,
    serial_dilute_test_compound,
    exposure_to_indicator_1,
    exposure_to_indicator_2,
    exposure_to_indicator_3
)
from pydantic import AnyUrl
from utils import log_assay_plate_incubation


class ReadAmesExperimentApplication(
    ExperimentApplication, 
):
    """Experiment application AMES Test LDRD experiment"""

    workflow_directory = Path("./workflows").resolve()
    protocol_directory = Path("./protocols").resolve()

    experiment_design = Path("./experiment_design.yaml")
    config = ExperimentApplicationConfig(node_url=AnyUrl("http://localhost:6000"))
    experiment_client = ExperimentClient()


    url = "http://hudson01:8000"


    # TODOs: 
    # Correct when new tip boxes and other supplies need to be swapped out. 

    def run_app(
            self,
            microplate_id,
        ):

            # TESTING
            print(f"START TIME: {int(time.time())}")

            print(f"MICROPLATE ID: {microplate_id}, {type(microplate_id)}")

            # workflow path(s)
            read_then_trash_384_well_plate_wf = self.workflow_directory / "read_then_trash_384_well_plate_wf.yaml"

            # other variables
            #exposure_incubation_time = 5400 # 5400 seconds = 90 min
            exposure_incubation_time = 1800 # 30 minutes for testing!!!
            microplate_incubation_time = 172800 # 172800 seconds = 48 hours
            # microplate_incubation_time = 86400 # 86400 seconds = 24 hours (used 03/19/26 to get a 72 hour timepoint reading)

            # initial payload
            parameters = {
                "temp": 37.0, # a float value setting the temperature of the Liconic Incubator (in Celsius)
                "humidity": 95.0, # a float value setting the humidity of the Liconic Incubator
                "shaker_speed": 30, # an integer value setting the shaker speed of the Liconic Incubator
                "stacker": 1, # an integer value specifying which stacker a well plate should be used in (Preferable to use "incubation_plate_id" : plate_id, where plate_id is an integer 1-88 - stacker and slot will be autocalculated)
                "slot": 2, # an integer value specifying which slot a well plate should be used in (Preferable to use "incubation_plate_id" : plate_id, where plate_id is an integer 1-88 - stacker and slot will be autocalculated)
                "tip_box_position": "5", # string of an integer 1-8 that identifies the position of the tip box when it is being refilled
                "seal_time": 3, # an integer value setting the time in seconds for the sealer to seal a plate
                "protocol_file": "", # string file path to the hso protocol file to be run on SOLO
            }

            # TESTING!!!
            print("Experiment App called to read and trash one plate!!!!")

            parameters["microplate_id"] = microplate_id

            # 1. Remove a 384-plate from incubator, remove lid, read in Hidex Sense, replace lid, and move to trash stack.
            workflow = self.workcell_client.submit_workflow(
                workflow_definition=read_then_trash_384_well_plate_wf,
                json_inputs={
                    "microplate_id": parameters["microplate_id"],
                }
            )
            # TESTING
            print("WORKFLOW")
            print(workflow)

            # collect hidex data  # DO NOT INCLUDE UNTIL BUG IS FIXED!
            hidex_datapoint_id = workflow.get_datapoint_id(step_key="hidex_data", label="file")
            print(f"{hidex_datapoint_id=}")


if __name__ == "__main__":

    current_time = datetime.datetime.now()

    experiment_app = ReadAmesExperimentApplication()

    with experiment_app.manage_experiment(
        run_name=f"Dion's Experiment Run {current_time}",
        run_description=f"Run for Dion's LDRD experiment, started at ~{current_time}",
    ):

        experiment_app.run_app()