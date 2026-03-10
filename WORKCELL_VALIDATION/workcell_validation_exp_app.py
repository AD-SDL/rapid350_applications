#!/usr/bin/env python3

"""
MADSci Experiment Application to validate that all instruments on RAPID 350 function correctly.
"""

import datetime
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
    solo_transfer1
)
from pydantic import AnyUrl


class WorkcellValidationApplication(ExperimentApplication):
    """Experiment application AMES Test LDRD experiment"""

    workflow_directory = Path("./workflows").resolve()
    protocol_directory = Path("./protocols").resolve()

    experiment_design = Path("./experiment_design.yaml")
    config = ExperimentApplicationConfig(node_url=AnyUrl("http://localhost:6000"))
    experiment_client = ExperimentClient()


    url = "http://hudson01:8000"

    def define_starting_resources(self): 
        """
        Creates and places MADSci labware resources at the correct locations 
        at the start of the experiment application.

        Starting resources layout: 
            SOLO nest 1: deepwell plate
            Stack1: 3 empty microplates with lid
                - Uses labware definition compatible with the PlateCrane module.
        """

        # Create and place the three microplate resources.
        microplates = []
        for i in range(1):   # ONLY MAKE ONE 96-WELL PLATE RESOURCE FOR WC VALIDATION
            # Create microplate lid resource.
            current_lid_resource = Resource(
                resource_name = f"microplate_lid_{i+1}",
                resource_description="microplate lid",
                attributes={
                    "lid": True
                }
            )

            # Create 384-well microplate resource.
            current_microplate_resource = Collection(
                resource_name = f"microplate_96well_{i+1}", 
                resource_description="96-well microplate resource used in the Demo experiment application.",
                capacity=2,
                children={
                    "lid_slot": Slot(
                        resource_name = "microplate_lid_slot",
                        children=[current_lid_resource]
                    )
                }
            )
            microplates.append(current_microplate_resource)

        stack_1_resource_id = self.location_client.get_location_by_name(location_name="Stack1").resource_id
        stack_1_resource = self.resource_client.get_resource(stack_1_resource_id)
        
        # FOR TESTING (remove from if block for real run!)
        if not len(stack_1_resource.children) == 1: 
            stack_1_resource.children = microplates   # NOTE: deletes any existing resource in the stack... a complete reset,
            # TODO: it might work better to just push the plate resource onto the stack...
            self.resource_client.update_resource(stack_1_resource)

    def run_app(self):

        # Workflow path(s)
        validation_wf = self.workflow_directory / "validation_wf.yaml"

        # Initial payload
        parameters = {
            "shaker_speed": 20, # an integer value setting the shaker speed of the Liconic Incubator
            "tip_box_position": "3", # string of an integer 1-8 that identifies the position of the tip box when it is being refilled
        }

        # Create starting resources
        self.define_starting_resources()


        # Prep SOLO protocol files
        package_hso(solo_transfer1.generate_hso_file, parameters, "/home/rpl/workspace/madsci_temp/validation_solo_temp1.hso")
        parameters["protocol_file"] = "/home/rpl/workspace/madsci_temp/validation_solo_temp1.hso"

        # Run the Workcell Validation Workflow
        workflow = self.workcell_client.submit_workflow(
            workflow_definition = validation_wf,
            file_inputs={
                "protocol_file": parameters["protocol_file"],
            },
            json_inputs={
                "tip_box_position": parameters["tip_box_position"],
                "shaker_speed": parameters["shaker_speed"]
            }
        )

        # Collect resulting 2 hidex data files 
        hidex_datapoint_1_id = workflow.get_datapoint_id(step_key="hidex_data_1", label="json_result")
        print(f"{hidex_datapoint_1_id=}")
        hidex_datapoint_2_id = workflow.get_datapoint_id(step_key="hidex_data_2", label="json_result")
        print(f"{hidex_datapoint_2_id=}")



if __name__ == "__main__":

    current_time = datetime.datetime.now()

    experiment_app = WorkcellValidationApplication()

    with experiment_app.manage_experiment(
        run_name=f"Workcell Validation experiment app {current_time}",
        run_description=f"Workcell validation experiment application, started at ~{current_time}",
    ):

        experiment_app.run_app()