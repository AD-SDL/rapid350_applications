#!/usr/bin/env python3

"""
Main MADSci Experiment Application for the AMES Test LDRD Project at Argonne National Laboratory.
"""

import datetime
from madsci.common.types.workflow_types import WorkflowDefinition
from madsci.common.types.step_types import StepDefinition
from madsci.client.experiment_application import ExperimentApplication
from pathlib import Path
import time

from helper_functions.hso_functions import package_hso
from protocols import (
    dispense_DMSO,
    dispense_control_and_test,
    serial_dilute_test_compound,
    dispense_cells_then_compound,
    exposure_to_indicator,
    dispense_into_384_plate
)


class DionExperimentApplication(ExperimentApplication):
    """Experiment application AMES Test LDRD experiment"""

    workflow_directory = Path("./workflows").resolve()
    protocol_directory = Path("./protocols").resolve()
    experiment_design = Path("./experiment_design.yaml")
    url = "http://hudson01:8000"

    def run_app(self):

        # workflow path(s)
        refill_tips_wf = self.workflow_directory / "refill_tips.yaml"
        run_solo_wf = self.workflow_directory / "run_solo.yaml"
        transfer_deepwell_to_incubator_wf = self.workflow_directory / "transfer_deepwell_to_incubator.yaml"
        transfer_deepwell_to_SOLO_wf = self.workflow_directory / "transfer_deepwell_to_SOLO.yaml"
        get_new_384_well_plate_wf = self.workflow_directory / "get_new_384_well_plate.yaml"
        transfer_384_to_incubator_wf = self.workflow_directory / "transfer_384_to_incubator.yaml"
        read_then_trash_384_well_plate_wf = self.workflow_directory / "read_then_trash_384_well_plate.yaml"

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

        # 1. Refill the tips at beginning of experiment run
        self.workcell_client.submit_workflow(
            workflow = refill_tips_wf,
            parameters=parameters
        )

        # 2. Run SOLO protocol: Dispense DMSO into dilution column wells.
        hso_1, hso_1_lines, hso_1_basename = package_hso(
            dispense_DMSO.generate_hso_file, parameters, "/home/rpl/wei_temp/solo_temp1.hso"
        )
        parameters["protocol_file"] = "/home/rpl/wei_temp/solo_temp1.hso"
        self.workcell_client.submit_workflow(
            workflow = run_solo_wf,
            parameters=parameters
        )

        # 3. Run SOLO protocol: Dispense control and test compounds into dilution column wells.
        hso_2, hso_2_lines, hso_2_basename = package_hso(
            dispense_control_and_test.generate_hso_file, parameters, "/home/rpl/wei_temp/solo_temp2.hso"
        )
        parameters["protocol_file"] = "/home/rpl/wei_temp/solo_temp2.hso"
        self.workcell_client.submit_workflow(
            workflow = run_solo_wf,
            parameters=parameters
        )

        # 4. Run SOLO protocol: Serial dilute test compound.
        hso_3, hso_3_lines, hso_3_basename = package_hso(
            serial_dilute_test_compound.generate_hso_file, parameters, "/home/rpl/wei_temp/solo_temp3.hso"
        )
        parameters["protocol_file"] = "/home/rpl/wei_temp/solo_temp3.hso"
        self.workcell_client.submit_workflow(
            workflow = run_solo_wf,
            parameters=parameters
        )

        # 5. Run SOLO protocol: Dispense cells then diluted compound into exposure wells (col 1,2,3)
        hso_4, hso_4_lines, hso_4_basename = package_hso(
            dispense_cells_then_compound.generate_hso_file, parameters, "/home/rpl/wei_temp/solo_temp4.hso"
        )
        parameters["protocol_file"] = "/home/rpl/wei_temp/solo_temp4.hso"
        self.workcell_client.submit_workflow(
            workflow = run_solo_wf,
            parameters=parameters
        )

        # 6. Seal the exposure/indicator deepwell and transfer into incubator.
        self.workcell_client.submit_workflow(
            workflow = transfer_deepwell_to_incubator_wf,
            parameters = parameters
        )

        # 7. Incubate at 37C for 90 min, with gentle shaking.
        time.sleep(exposure_incubation_time)

        # 8. Unload exposure/indicator deepwell from incubator and return to SOLO deck 1.
        self.workcell_client.submit_workflow(
            workflow = transfer_deepwell_to_SOLO_wf,
            parameters = parameters
        )

        # 9. Run SOLO protocol: Transfer all contents of exposure wells to indicator wells.
        hso_5, hso_5_lines, hso_5_basename = package_hso(
            exposure_to_indicator.generate_hso_file, parameters, "/home/rpl/wei_temp/solo_temp5.hso"
        )
        parameters["protocol_file"] = "/home/rpl/wei_temp/solo_temp5.hso"
        self.workcell_client.submit_workflow(
            workflow = run_solo_wf,
            parameters=parameters
        )

        # BEGIN LOOP: Loop 3 times to create 3 384-well assay plates.
        for i in range(3):
            microplate_id = i + 2  # 384 well plates will have plate IDs 2, 3, and 4
            parameters["microplate_id"] = str(microplate_id)

            # 10. Transfer a new 384 well plate to the SOLO deck
            self.workcell_client.submit_workflow(
                workflow = get_new_384_well_plate_wf,
                parameters=parameters
            )

            # 11. Run SOLO protocol: Transfer 50uL from indicator wells into each well of a 384-well plate
            parameters["current_indicator_column"] = i + 4  # indicator columns are 4, 5, and 6

            # 11a. First half of 384-well plate
            parameters["half"] = 1
            solo_temp_filename = f"/home/rpl/wei_temp/solo_temp_384_{i+5}.hso"
            hso_6, hso_6_lines, hso_6_basename = package_hso(
                dispense_into_384_plate.generate_hso_file,
                payload=parameters,
                temp_file_path=solo_temp_filename,
            )
            parameters["protocol_file"] = solo_temp_filename
            self.workcell_client.submit_workflow(
                workflow = run_solo_wf,
                parameters=parameters
            )

            # 11b. Second half of 384 well plate
            parameters["half"] = 2
            solo_temp_filename = f"/home/rpl/wei_temp/solo_temp_384_{i+6}.hso"
            hso_7, hso_7_lines, hso_7_basename = package_hso(
                dispense_into_384_plate.generate_hso_file,
                payload=parameters,
                temp_file_path=solo_temp_filename,
            )
            parameters["protocol_file"] = solo_temp_filename
            self.workcell_client.submit_workflow(
                workflow = run_solo_wf,
                parameters=parameters
            )

            # 12. Replace lid on 384-well plate and transfer into incubator
            self.workcell_client.submit_workflow(
                workflow = transfer_384_to_incubator_wf,
                parameters=parameters
            )

        # END LOOP. 
        # NOTE: At this point, all three 384-well assay plates are in the incubator and shaking.

        # 13. Incubate all 3 384-well plates overnight (48 hours, no shaking, 37C).
        time.sleep(micoplate_incubation_time)

        # BEGIN LOOP. Collect absorbance readings for each of the 3 384-well plates and transfer them to trash stack.
        for i in range(3):
            microplate_id = i + 2 # 384 well plates will have plate IDs 2, 3, and 4
            parameters["microplate_id"] = str(microplate_id)

            # 14. Remove a 384-plate from incubator, remove lid, read in Hidex Sense, replace lid, and move to trash stack
            self.workcell_client.submit_workflow(
                workflow = read_then_trash_384_well_plate_wf,
                parameters=parameters
            )

        # END LOOP. 
        # NOTE: At this point, all three 384-well plates are in the trash stack.


if __name__ == "__main__":

    current_time = datetime.datetime.now()

    experiment_app = DionExperimentApplication()

    with experiment_app.manage_experiment(
        run_name=f"Dion's Experiment Run {current_time}",
        run_description=f"Run for Dion's LDRD experiment, started at ~{current_time}",
    ):

        experiment_app.run_app()