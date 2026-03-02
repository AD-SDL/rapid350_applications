#!/usr/bin/env python3

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
    exposure_to_indicator,
    serial_dilute_test_compound,
)
from pydantic import AnyUrl


class DionExperimentApplication(ExperimentApplication):
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

        # Create and place deep well resource. 
        deep_well_lid_resource = Resource(
                resource_name = f"AMES_deep_well_lid",
                resource_description="deep well lid",
                attributes={
                    "lid": True
                }
            )
        deep_well_48_resource = Collection(
            resource_name="AMES_deep_well_48",
            resource_description="48-well deep well plate resource",
            capacity=2,
            children={
                    "lid_slot": Slot(
                        resource_name = "deep_well_lid_slot",
                        children=[deep_well_lid_resource]
                    )
                }
        )
        try: 
            solo_nest_1_resource_id = self.location_client.get_location_by_name(location_name="Solo.Position1").resource_id
            solo_nest_1_resource = self.resource_client.get_resource(solo_nest_1_resource_id)
            self.resource_client.push(
                resource=solo_nest_1_resource,
                child=deep_well_48_resource,
            )
        except Exception as e: 
            print(f"Solo.Position1 is already full. Cannot push new deep well resource.")
            #raise e

        # Create and place the three microplate resources.
        microplates = []
        for i in range(3): 
            # Create microplate lid resource.
            current_lid_resource = Resource(
                resource_name = f"AMES_microplate_lid_{i+1}",
                resource_description="microplate lid",
                attributes={
                    "lid": True
                }
            )

            # Create 384-well microplate resource.
            current_microplate_resource = Collection(
                resource_name = f"AMES_microplate_384well_{i+1}", 
                resource_description="384-well microplate resource used in the AMES Test Experiment Application",
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
        if not len(stack_1_resource.children) == 3: 
            stack_1_resource.children = microplates   # NOTE: deletes any existing resource in the stack... a complete reset,
            # TODO: it might work better to just push the plate resource onto the stack...
            self.resource_client.update_resource(stack_1_resource)


    def run_app(self):

        # workflow path(s)
        refill_tips_wf = self.workflow_directory / "refill_tips_wf.yaml"
        run_solo_wf = self.workflow_directory / "run_solo_wf.yaml"
        transfer_deepwell_to_incubator_wf = self.workflow_directory / "transfer_deepwell_to_incubator_wf.yaml"
        transfer_deepwell_to_SOLO_wf = self.workflow_directory / "transfer_deepwell_to_SOLO_wf.yaml"
        get_new_384_well_plate_wf = self.workflow_directory / "get_new_384_well_plate_wf.yaml"
        transfer_384_to_incubator_wf = self.workflow_directory / "transfer_384_to_incubator_wf.yaml"
        read_then_trash_384_well_plate_wf = self.workflow_directory / "read_then_trash_384_well_plate_wf.yaml"

        # other variables
        exposure_incubation_time = 5400 # 5400 seconds = 90 min
        micoplate_incubation_time = 172800 # 172800 seconds = 48 hours

        # initial payload
        parameters = {
            "temp": 37.0, # a float value setting the temperature of the Liconic Incubator (in Celsius)
            "humidity": 95.0, # a float value setting the humidity of the Liconic Incubator
            "shaker_speed": 20, # an integer value setting the shaker speed of the Liconic Incubator
            "stacker": 1, # an integer value specifying which stacker a well plate should be used in (Preferable to use "incubation_plate_id" : plate_id, where plate_id is an integer 1-88 - stacker and slot will be autocalculated)
            "slot": 2, # an integer value specifying which slot a well plate should be used in (Preferable to use "incubation_plate_id" : plate_id, where plate_id is an integer 1-88 - stacker and slot will be autocalculated)
            "tip_box_position": "5", # string of an integer 1-8 that identifies the position of the tip box when it is being refilled
            "seal_time": 3, # an integer value setting the time in seconds for the sealer to seal a plate
            "protocol_file": "", # string file path to the hso protocol file to be run on SOLO
        }

        # Create starting resources.  # WORKS
        self.define_starting_resources()

        # NOTE: Cannot use lids! They do not fit in the incubator!

        # 1. Refill the tips at beginning of experiment run  # WORKS
        self.workcell_client.submit_workflow(
            workflow_definition = refill_tips_wf,
            json_inputs={
                "tip_box_position": parameters["tip_box_position"],
            }
        )

        # 2. Run SOLO protocol: Dispense DMSO into dilution column wells.  # WORKS
        hso_1, hso_1_lines, hso_1_basename = package_hso(
            dispense_DMSO.generate_hso_file, parameters, "/home/rpl/workspace/madsci_temp/solo_temp1.hso"
        )
        parameters["protocol_file"] = "/home/rpl/workspace/madsci_temp/solo_temp1.hso"
        self.workcell_client.submit_workflow(
            workflow_definition = run_solo_wf,
            file_inputs={
                "protocol_file": parameters["protocol_file"],
            }
        )

        # 3. Run SOLO protocol: Dispense control and test compounds into dilution column wells.  # WORKS
        hso_2, hso_2_lines, hso_2_basename = package_hso(
            dispense_control_and_test.generate_hso_file, parameters, "/home/rpl/workspace/madsci_temp/solo_temp2.hso"
        )
        parameters["protocol_file"] = "/home/rpl/workspace/madsci_temp/solo_temp2.hso"
        self.workcell_client.submit_workflow(
            workflow_definition = run_solo_wf,
            file_inputs={
                "protocol_file": parameters["protocol_file"],
            }
        )

        # 4. Run SOLO protocol: Serial dilute test compound.  # WORKS
        hso_3, hso_3_lines, hso_3_basename = package_hso(
            serial_dilute_test_compound.generate_hso_file, parameters, "/home/rpl/workspace/madsci_temp/solo_temp3.hso"
        )
        parameters["protocol_file"] = "/home/rpl/workspace/madsci_temp/solo_temp3.hso"
        self.workcell_client.submit_workflow(
            workflow_definition = run_solo_wf,
            file_inputs={
                "protocol_file": parameters["protocol_file"],
            }
        )

        # 5. Run SOLO protocol: Dispense cells then diluted compound into exposure wells (col 1,2,3)  # WORKS
        hso_4, hso_4_lines, hso_4_basename = package_hso(
            dispense_cells_then_compound.generate_hso_file, parameters, "/home/rpl/workspace/madsci_temp/solo_temp4.hso"
        )
        parameters["protocol_file"] = "/home/rpl/workspace/madsci_temp/solo_temp4.hso"
        self.workcell_client.submit_workflow(
            workflow_definition = run_solo_wf,
            file_inputs={
                "protocol_file": parameters["protocol_file"],
            }
        )

        # 6. Seal the exposure/indicator deepwell and transfer into incubator.  # WORKS EXCEPT FOR SEALER
        # TODO: SEALER BROKEN - REPLACE THE VACUUM CUPS
        self.workcell_client.submit_workflow(
            workflow_definition = transfer_deepwell_to_incubator_wf,
            json_inputs={
                "shaker_speed": parameters["shaker_speed"],
            }
        )

        # 7. Incubate at 37C for 90 min, with gentle shaking.  # WORKING
        time.sleep(exposure_incubation_time)

        # 8. Unload exposure/indicator deepwell from incubator and return to SOLO deck 1.  # WORKS
        self.workcell_client.submit_workflow(
            workflow_definition = transfer_deepwell_to_SOLO_wf,
        )

        # 9. Run SOLO protocol: Transfer all contents of exposure wells to indicator wells.
        hso_5, hso_5_lines, hso_5_basename = package_hso(
            exposure_to_indicator.generate_hso_file, parameters, "/home/rpl/workspace/madsci_temp/solo_temp5.hso"
        )
        parameters["protocol_file"] = "/home/rpl/workspace/madsci_temp/solo_temp5.hso"  # EDITED, NOT TESTED
        self.workcell_client.submit_workflow(
            workflow_definition = run_solo_wf,
            file_inputs={
                "protocol_file": parameters["protocol_file"],
            }
        )

        # # BEGIN LOOP: Loop 3 times to create 3 384-well assay plates.
        # for i in range(3):
        for i in range(1):  # TESTING
            microplate_id = i + 2  # 384 well plates will have plate IDs 2, 3, and 4
            parameters["microplate_id"] = str(microplate_id)

            # 10. Transfer a new 384 well plate to the SOLO deck. # WORKS
            self.workcell_client.submit_workflow(
                workflow_definition = get_new_384_well_plate_wf,
            )

            # 11. Run SOLO protocol: Transfer 50uL from indicator wells into each well of a 384-well plate
            parameters["current_indicator_column"] = i + 4  # indicator columns are 4, 5, and 6

            # 11a. First half of 384-well plate. # EDITED, NOT TESTED
            parameters["half"] = 1
            solo_temp_filename = f"/home/rpl/workspace/madsci_temp/solo_temp_384_{i+5}.hso"
            hso_6, hso_6_lines, hso_6_basename = package_hso(
                dispense_into_384_plate.generate_hso_file,
                payload=parameters,
                temp_file_path=solo_temp_filename,
            )
            parameters["protocol_file"] = solo_temp_filename
            self.workcell_client.submit_workflow(
                workflow_definition = run_solo_wf,
                file_inputs={
                    "protocol_file": parameters["protocol_file"],
                }
            )

            # 11b. Second half of 384 well plate # EDITED, NOT TESTED
            parameters["half"] = 2
            solo_temp_filename = f"/home/rpl/workspace/madsci_temp/solo_temp_384_{i+6}.hso"
            hso_7, hso_7_lines, hso_7_basename = package_hso(
                dispense_into_384_plate.generate_hso_file,
                payload=parameters,
                temp_file_path=solo_temp_filename,
            )
            parameters["protocol_file"] = solo_temp_filename
            self.workcell_client.submit_workflow(
                workflow_definition = run_solo_wf,
                file_inputs={
                    "protocol_file": parameters["protocol_file"],
                }
            )

            # 12. Replace lid on 384-well plate and transfer into incubator # WORKS
            self.workcell_client.submit_workflow(
                workflow_definition = transfer_384_to_incubator_wf,
                json_inputs={
                    "microplate_id": parameters["microplate_id"],
                }
            )

        # # END LOOP.
        # # NOTE: At this point, all three 384-well assay plates are in the incubator and shaking.

        # 13. Incubate all 3 384-well plates overnight (48 hours, no shaking, 37C).  # WORKS
        time.sleep(micoplate_incubation_time)

        # # BEGIN LOOP. Collect absorbance readings for each of the 3 384-well plates and transfer them to trash stack.
        # for i in range(3):
        for i in range(1):  # TESTING
            microplate_id = i + 2 # 384 well plates will have plate IDs 2, 3, and 4
            parameters["microplate_id"] = str(microplate_id)

            # 14. Remove a 384-plate from incubator, remove lid, read in Hidex Sense, replace lid, and move to trash stack.
            # WORKS EXCEPT FOR HIDEX: Bug? Won't return from run assay. Probably related to automatic saving of files in a specific folder.
            workflow = self.workcell_client.submit_workflow(
                workflow_definition=read_then_trash_384_well_plate_wf,
                json_inputs={
                    "microplate_id": parameters["microplate_id"],
                }
            )
            # # collect hidex data
            # hidex_datapoint_id = workflow.get_datapoint_id(step_key="hidex_data", label="json_result")
            # print(f"{hidex_datapoint_id=}")


        # # END LOOP.
        # # NOTE: At this point, all three 384-well plates are in the trash stack.


if __name__ == "__main__":

    current_time = datetime.datetime.now()

    experiment_app = DionExperimentApplication()

    with experiment_app.manage_experiment(
        run_name=f"Dion's Experiment Run {current_time}",
        run_description=f"Run for Dion's LDRD experiment, started at ~{current_time}",
    ):

        experiment_app.run_app()