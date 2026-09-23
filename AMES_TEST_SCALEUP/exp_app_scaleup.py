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
    serial_dilute_test_compound,
    exposure_to_indicator_1,
    exposure_to_indicator_2,
    exposure_to_indicator_3
)
from pydantic import AnyUrl


class AMESExperimentApplication(
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



    def create_deepwell_48_resource(
        self,
        set_num: int = 1,
        exp_num: int = 1,
    ): 
        """
        Creates and places a MADSci labware resource for a 48-deepwell plate at 
        SOLO Position 1.

        # NOTE: Cannot use lids! They do not fit in the incubator!

        """
        deep_well_48_resource = Collection(
            resource_name=f"AMES_deep_well_48_set{set_num}_exp{exp_num}",
            resource_description=f"48-well deep well plate resource set {set_num}, experiment {exp_num}",
            capacity=2,
            children={},
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


    def create_assay_384_resources(
        self, 
        set_num: int = 1,
        exp_num: int = 1,
    ):
        """
        Creates and places MADSci labware resources for 3 x 384-well assay plates with lids in Stack 1
            - Uses labware definition compatible with the PlateCrane module.
        """
        # Create and place the three microplate resources.
        microplates = []
        for i in range(3):
            # Create microplate lid resource.
            current_lid_resource = Resource(
                resource_name = f"AMES_microplate_lid_set{set_num}_exp{exp_num}_plate{i+1}",
                resource_description="microplate lid",
                attributes={
                    "lid": True
                }
            )

            # Create 384-well microplate resource.
            current_microplate_resource = Collection(
                resource_name = f"AMES_microplate_384well_set{set_num}_exp{exp_num}_plate{i+1}",
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
        stack_1_resource.children = microplates   # NOTE: deletes any existing resource in the stack... a complete reset,
        # TODO: it might work better to just push the plate resource onto the stack...
        self.resource_client.update_resource(stack_1_resource)



    def run_app(
        self,
        dmso_stock_columns,
        dilution_plate_columns, 
        cell_stock_columns, 
        control_compound_wells,
        control_plate_location,
        test_compound_wells,
        test_plate_location,
        exposure_indicator_incubator_ids,
        assay_384_well_incubator_ids,
        experiment_set: int = 1,

    ):

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
        print("EXPERIMENT APP CALLED!!!!")

        print("CONFIG")
        print(f"{self.config}")

        print("INPUT VARIABLES!!!")   # WORKS!
        print(f"{experiment_set=}")
        print(f"{dmso_stock_columns=}")
        print(f"{dilution_plate_columns=}")
        print(f"{cell_stock_columns=}")
        print(f"{control_compound_wells=}")
        print(f"{control_compound_wells=}")
        print(f"{test_compound_wells=}")
        print(f"{test_compound_wells=}")
        print(f"{exposure_indicator_incubator_ids=}")
        print(f"{assay_384_well_incubator_ids=}")

        exposure_indicator_incubation_start_times = []

        # 1. Refill the tips at beginning of experiment run 
        self.workcell_client.submit_workflow(
            workflow_definition = refill_tips_wf,
            json_inputs={
                "tip_box_position": parameters["tip_box_position"],
            }
        )

        # START LOOP: Create two exposure/indicator plates and incubate
        for i in range(2): 
        # for i in range(1):  # FOR TESTING!

            print("***********************")
            print(f"{i=}")

            # Set variables for current round
            parameters["dmso_stock_column"] = dmso_stock_columns[i]
            parameters["dilution_column"] = dilution_plate_columns[i]
            parameters["control_compound_well"] = control_compound_wells[i]
            parameters["test_compound_well"] = test_compound_wells[i]
            parameters["control_plate_location"] = control_plate_location
            parameters["test_plate_location"] = test_plate_location
            parameters["cell_stock_column"] = cell_stock_columns[i]
            parameters["exp_ind_plate_id"] = exposure_indicator_incubator_ids[i]
            
            # 2. Create starting resources.
            self.create_deepwell_48_resource(
                set_num=experiment_set,
                exp_num=i+1,
            )
            print(f"Created EXP/IND resource w/ set = {experiment_set}, exp = {i+1}")

            # 3. Run SOLO protocol: Dispense DMSO into dilution column wells.  # WORKS!
            hso_1, hso_1_lines, hso_1_basename = package_hso(
                dispense_DMSO.generate_hso_file, parameters, f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_1.hso"
            )
            parameters["protocol_file"] = f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_1.hso"
            self.workcell_client.submit_workflow(
                workflow_definition = run_solo_wf,
                file_inputs={
                    "protocol_file": parameters["protocol_file"],
                }
            )

            # 4. Run SOLO protocol: Dispense control and test compounds into dilution column wells.  # WORKS!
            hso_2, hso_2_lines, hso_2_basename = package_hso(
                dispense_control_and_test.generate_hso_file, parameters, f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_2.hso"
            )
            parameters["protocol_file"] = f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_2.hso"
            self.workcell_client.submit_workflow(
                workflow_definition = run_solo_wf,
                file_inputs={
                    "protocol_file": parameters["protocol_file"],
                }
            )

            # 5. Run SOLO protocol: Serial dilute test compound.  # WORKS!
            hso_3, hso_3_lines, hso_3_basename = package_hso(
                serial_dilute_test_compound.generate_hso_file, parameters, f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_3.hso"
            )
            parameters["protocol_file"] = f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_3.hso"
            self.workcell_client.submit_workflow(
                workflow_definition = run_solo_wf,
                file_inputs={
                    "protocol_file": parameters["protocol_file"],
                }
            )

            # 6. Run SOLO protocol: Dispense cells then diluted compound into exposure wells (col 1,2,3)  # WORKS!
            hso_4, hso_4_lines, hso_4_basename = package_hso(
                dispense_cells_then_compound.generate_hso_file, parameters, f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_4.hso"
            )
            parameters["protocol_file"] = f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_4.hso"
            self.workcell_client.submit_workflow(
                workflow_definition = run_solo_wf,
                file_inputs={
                    "protocol_file": parameters["protocol_file"],
                }
            )

            # TODO: TEST
            # 7. Seal the exposure/indicator deepwell and transfer into incubator.
            self.workcell_client.submit_workflow(
                workflow_definition = transfer_deepwell_to_incubator_wf,
                json_inputs={
                    "shaker_speed": parameters["shaker_speed"],
                    "plate_id": parameters["exp_ind_plate_id"]
                }
            )
            # Record incubation start time for exp/ind plate.
            exposure_indicator_incubation_start_times.append(int(time.time()))

            # Wait for user to replace labware before continuing. 
            # TODO: Check which labware needs to be replaced here. 
            print("############################################################")
            print("PLEASE PLACE THE NEXT EXPOSURE/INDICATOR PLATE AT SOLO POSITION 1.")
            input("Press Enter to continue when this is complete.")

        # TESTING: 
        print(f"Incubation start times: {exposure_indicator_incubation_start_times}")


        # Wait for user to replace labware before continuing. 
        # TODO: Check which labware needs to be replaced here. 
        print("############################################################")
        print("PLEASE REPLACE THE TIP BOX AT SOLO POSITION 5.")
        input("Press Enter to continue when this is complete.")

        # 8. Refill the tips before the exposure to indicator transfers
        self.workcell_client.submit_workflow(
            workflow_definition = refill_tips_wf,
            json_inputs={
                "tip_box_position": parameters["tip_box_position"],
            }
        )

        

        # BEGIN LOOP TO CREATE 384-well ASSAY PLATES
        all_assay_384_incubation_start_times = []
        for i in range(2): 

            # Reset variables for new loop:
            # TODO: Which of these do we need to reset? 
            parameters["dmso_stock_column"] = dmso_stock_columns[i]
            parameters["dilution_column"] = dilution_plate_columns[i]
            parameters["control_compound_well"] = control_compound_wells[i]
            parameters["test_compound_well"] = test_compound_wells[i]
            parameters["control_plate_location"] = control_plate_location
            parameters["test_plate_location"] = test_plate_location
            parameters["cell_stock_column"] = cell_stock_columns[i]
            parameters["exp_ind_plate_id"] = exposure_indicator_incubator_ids[i]

            # Wait for the associated exp/ind incubation to finish before starting loop to create 3 assay plates 
            # 9. Incubate at 37C for 90 min, with gentle shaking.
            # print(f"Incubating for {exposure_incubation_time} seconds.")
            while time.time() - exposure_indicator_incubation_start_times[i] < exposure_incubation_time:
                print(f"Incubating. Continuing in {int(exposure_incubation_time - (time.time() - exposure_indicator_incubation_start_times[i]))} seconds.")
                time.sleep(5)

                if time.time() - exposure_indicator_incubation_start_times[i] >= exposure_incubation_time:
                    print("Incubation complete")
                    break

            # 10. Create 3 x 384-well assay plate MADSci resources and place into Stack 1
            # TODO: TEST!
            self.create_assay_384_resources(
                set_num=experiment_set,
                exp_num=i+1,
            )

            # TODO: TEST INCUBATOR PLATE ID CHANGE!
            # 11. Unload exposure/indicator deepwell from incubator and return to SOLO deck 1.
            self.workcell_client.submit_workflow(
                workflow_definition = transfer_deepwell_to_SOLO_wf,
                json_inputs={
                    "plate_id": parameters["exp_ind_plate_id"]
                }
            )

            # NOTE: No changes needed for multi run!
            # 12a. Run SOLO protocol: Transfer FIRST exposure column to FIRST indicator column and MIX WELL
            hso_5, hso_5_lines, hso_5_basename = package_hso(
                exposure_to_indicator_1.generate_hso_file, parameters, f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_5.hso"
            )
            parameters["protocol_file"] = f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_5.hso"
            self.workcell_client.submit_workflow(
                workflow_definition = run_solo_wf,
                file_inputs={
                    "protocol_file": parameters["protocol_file"],
                }
            )

            # NOTE: No changes needed for multi run!
            # 12b. Run SOLO protocol: Transfer SECOND exposure column to SECOND indicator column and MIX WELL
            hso_6, hso_6_lines, hso_6_basename = package_hso(
                exposure_to_indicator_2.generate_hso_file, parameters, f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_6.hso"
            )
            parameters["protocol_file"] = f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_6.hso"
            self.workcell_client.submit_workflow(
                workflow_definition = run_solo_wf,
                file_inputs={
                    "protocol_file": parameters["protocol_file"],
                }
            )

            # NOTE: No changes needed for multi run!
            # 12c. Run SOLO protocol: Transfer THIRD exposure column to THIRD indicator column and MIX WELL
            hso_7, hso_7_lines, hso_7_basename = package_hso(
                exposure_to_indicator_3.generate_hso_file, parameters, f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_7.hso"
            )
            parameters["protocol_file"] = f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_7.hso"
            self.workcell_client.submit_workflow(
                workflow_definition = run_solo_wf,
                file_inputs={
                    "protocol_file": parameters["protocol_file"],
                }
            )

            current_round_assay_incubation_start_times = []
            for j in range(3):
                parameters["microplate_id"] = str(exposure_indicator_incubator_ids[i][j])

                # 13. Transfer a new 384 well plate to the SOLO deck.
                self.workcell_client.submit_workflow(
                    workflow_definition = get_new_384_well_plate_wf,
                )

                # 14. Run SOLO protocol: Transfer 50uL from indicator wells into each well of a 384-well plate
                parameters["current_indicator_column"] = j + 4  # indicator columns are 4, 5, and 6

                # 14a. First half of 384-well plate.
                parameters["half"] = 1
                solo_temp_filename = f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_{j+8}.hso"
                hso_8, hso_8_lines, hso_8_basename = package_hso(
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

                # 14b. Second half of 384 well plate
                parameters["half"] = 2
                solo_temp_filename = f"/home/rpl/workspace/madsci_temp/solo_temp_set{str(experiment_set)}_exp{i+1}_{j+9}.hso"
                hso_9, hso_9_lines, hso_9_basename = package_hso(
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

                # 15. Replace lid on 384-well plate and transfer into incubator
                self.workcell_client.submit_workflow(
                    workflow_definition = transfer_384_to_incubator_wf,
                    json_inputs={
                        "microplate_id": parameters["microplate_id"],
                    }
                )

                # Add incubation start time to list.
                current_round_assay_incubation_start_times.append(int(time.time()))

                # END LOOP to create 3 x 384-well assay plates
            
            all_assay_384_incubation_start_times.append(current_round_assay_incubation_start_times)

        print("ALL ASSAY INCUBATION START TIMES")
        print(all_assay_384_incubation_start_times)

        # END LOOP to handle both exp/ind plates and create 3 assay plates for each exp/ind plate.
        # NOTE: At this point, all three 384-well assay plates are in the incubator and shaking.

        # TODO: Add end shaking here to stop the microplate side from shaking.

        for i in range(2): 

            # Reset variables for new loop:
            # TODO: Which of these do we need to reset? 
            parameters["dmso_stock_column"] = dmso_stock_columns[i]
            parameters["dilution_column"] = dilution_plate_columns[i]
            parameters["control_compound_well"] = control_compound_wells[i]
            parameters["test_compound_well"] = test_compound_wells[i]
            parameters["control_plate_location"] = control_plate_location
            parameters["test_plate_location"] = test_plate_location
            parameters["cell_stock_column"] = cell_stock_columns[i]
            parameters["exp_ind_plate_id"] = exposure_indicator_incubator_ids[i]

            for j in range(3):

                parameters["microplate_id"] = exposure_indicator_incubator_ids[i][j]

                # 16. Wait for incubation to complate for each assay plate
                # TODO: TEST!
                while time.time() - all_assay_384_incubation_start_times[i][j] < microplate_incubation_time:
                    print(f"Incubating. Continuing in {int(microplate_incubation_time - (time.time() - all_assay_384_incubation_start_times[i][j]))} seconds.")
                    time.sleep(5)

                    if time.time() - all_assay_384_incubation_start_times[i][j] >= microplate_incubation_time:
                        print("Incubation complete")
                        break

                # 17. Remove a 384-plate from incubator, remove lid, read in Hidex Sense, replace lid, and move to trash stack.
                workflow = self.workcell_client.submit_workflow(
                    workflow_definition=read_then_trash_384_well_plate_wf,
                    json_inputs={
                        "microplate_id": parameters["microplate_id"],
                    }
                )
                # collect hidex data  # DO NOT INCLUDE UNTIL BUG IS FIXED!
                hidex_datapoint_id = workflow.get_datapoint_id(step_key="hidex_data", label="file")
                print(f"{hidex_datapoint_id=}")

            # END LOOP: Done reading all assay plates in one set

        # END LOOP: Done reading all assay plates in both sets. 
        # NOTE: At this point, all three 384-well plates are in the trash stack.


if __name__ == "__main__":

    current_time = datetime.datetime.now()

    experiment_app = AMESExperimentApplication()

    with experiment_app.manage_experiment(
        run_name=f"Dion's Experiment Run {current_time}",
        run_description=f"Run for Dion's LDRD experiment, started at ~{current_time}",
    ):

        experiment_app.run_app()