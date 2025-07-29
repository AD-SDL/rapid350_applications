#!/usr/bin/env python3
"""Converted to MADSci"""

# general imports
from datetime import datetime, timedelta
from pathlib import Path
import time

# MADSci imports
from madsci.common.types.workflow_types import WorkflowDefinition
from madsci.common.types.step_types import StepDefinition
from madsci.client.experiment_application import ExperimentApplication

# helper funtion imports
from helper_functions import parse_run_details_csv
from helper_functions.hso_functions import package_hso

# protocol imports 
from protocols import solo_step1, solo_step2, solo_step3
from tools.hudson_solo_auxillary.hso_functions import package_hso


class MultiPlateAMPExperimentApplication(ExperimentApplication):
    """Growth curve experiment application for the multi plate AMP LDRD project"""

    # which workcell to use
    url = "http://hudson01:8000"

    # important paths
    workflow_directory = Path("./workflows").resolve()
    protocol_directory = Path("./protocols").resolve()
    experiment_design = Path("./experiment_design.yaml")


    def run_app(self): 

        # extract run_id. # TODO how?
        experiment_id = self.Experiment.experiment_id  # TEST THIS

        # workflow paths
        workcell_setup_wf = workflow_directory / "workcell_setup.yaml"
        refill_tips_wf = workflow_directory / "refill_tips.yaml"
        T0_wf = workflow_directory / "create_plate_T0.yaml"
        T12_wf = workflow_directory / "read_plate_T12.yaml"

        # run details path
        # TODO: pass this in as an argument
        run_details_csv_path = app_dir / "run_details.csv"

        # variables and parameters setup
        num_assay_plates = None
        parameters = {
            "temp": 37.0,  # a float value setting the temperature of the Liconic Incubator (in Celsius)
            "humidity": 95.0,  # a float value setting the humidity of the Liconic Incubator
            "shaker_speed": 20,  # an integer value setting the shaker speed of the Liconic Incubator
            "tip_box_position": "1",  # string of an integer 1-8 that identifies the position of the tip box when it is being refilled
        }

        # parse the run details csv and add the information to the parameters dict
        run_details = parse_run_details_csv(run_details_csv_path)
        num_assay_plates = run_details[0]
        incubation_hours = run_details[1]
        parameters["treatment_stock_column"] = run_details[2]
        parameters["culture_stock_column"] = run_details[3]
        parameters["culture_dilution_column"] = run_details[4]
        parameters["media_stock_start_column"] = run_details[5]
        parameters["treatment_dilution_half"] = run_details[6]

        # run Workcell Setup Workflow (preheat the hidex to 37C)
        self.workcell_client.submit_workflow(
            workflow = workcell_setup_wf, 
            parameters=parameters,
            await_completion=False,
        )

        # START T0 LOOP
        for i in range(num_assay_plates):
            """Loop to create assay plates and take T0 absorbance readings"""

            parameters["current_assay_plate_num"] = i + 1
            parameters["plate_id"] = str(i + 1)

            print(f"Current assay plate number: {parameters['current_assay_plate_num']}")
            print(f"Plate ID: {parameters['plate_id']}")

            # generate temp hso files (for SOLO liquid handler)
            hso_1_path = package_hso(
                solo_step1.generate_hso_file,
                payload,
                "/home/rpl/wei_temp/solo_temp1.hso"
            )
            hso_2_path = package_hso(
                solo_step2.generate_hso_file,
                payload,
                "/home/rpl/wei_temp/solo_temp2.hso"
            )
            hso_3_path = package_hso(
                solo_step3.generate_hso_file,
                payload,
                "/home/rpl/wei_temp/solo_temp3.hso"
            )

            # Save the temp hso file paths into the payload
            parameters["hso_1_path"] = hso_1_path
            parameters["hso_2_path"] = hso_2_path
            parameters["hso_3_path"] = hso_3_path

            # refill the tips (software step) before every two assay plates
            if (i % 2) == 0:
                self.workcell_client.submit_workflow(
                    workflow=refill_tips_wf,
                    parameters=parameters,
                )

            # run the T0 workflow  
            # TODO: How do we collect Hidex data files now in MADSci?
            workflow_info = self.workcell_client.submit_workflow(
                workflow=T0_wf,
                parameters=parameters,
            )

            # collect the Hidex Sense data from the workflow info.  # TODO: TEST THIS
            output_dir = Path.home() / "runs" / str(experiment_id)
            output_dir.mkdir(parents=True, exist_ok=True)
            self.data_client.save_datapoint_value(
                workflow_info.get_datapoint_id_by_label("T0_result"),
                output_dir / f"T0_result_{parameters'plate_id']}.xlsx",
            )
        # END T0 LOOP

        # calculate then sleep for total incubation time
        incubation_seconds = incubation_hours * 3600
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=incubation_seconds - (2160 * (num_assay_plates -1)))

        # TESTING
        print(f"incubation_hours: {incubation_hours}")
        print(f"incubation_seconds: {incubation_seconds}")
        print(f"starting sleep at {start_time.strftime('%I:%M:%S %p')}")
        print(f"ending sleep at {end_time.strftime('%I:%M:%S %p')}")
        print(f"Now sleeping for {incubation_seconds - (2159 * (num_assay_plates -1))} seconds")

        # Sleep for the total incubation time
        time.sleep(incubation_seconds - (2160 * (num_assay_plates - 1)))  # T0 portion takes ~36 min to run (2160 seconds)

        # START T12 (or endpoint) LOOP
        for i in range(num_assay_plates):
            """Loop to read all assay plates"""

            parameters["current_assay_plate_num"] = i + 1
            parameters["plate_id"] = str(i + 1)

            # Testing
            print(f"Current assay plate number: {parameters['current_assay_plate_num']}")
            print(f"Plate ID: {parameters['plate_id']}")

            # Run the T12 workflow
            workflow_info = workcell_client.submit_workflow(
                workflow=T12_wf,
                parameters=parameters,
            )

            # collect the Hidex Sense data from the workflow info.  # TODO: TEST THIS
            output_dir = Path.home() / "runs" / str(experiment_id)
            output_dir.mkdir(parents=True, exist_ok=True)
            self.data_client.save_datapoint_value(
                workflow_info.get_datapoint_id_by_label("endpoint_result"),
                output_dir / f"endpoint_result_{parameters['plate_id']}.xlsx",
            )

            # Wait to run the next assay plate (Assay plate took ~36 min to create and T0 read but T12 reading only takes ~9min )
            if i != num_assay_plates - 1:

                # Print information about incubation time
                start_time = datetime.now()
                end_time = start_time + timedelta(seconds=1620)
                print(f"starting sleep at {start_time.strftime('%I:%M:%S %p')}")
                print(f"ending sleep at {end_time.strftime('%I:%M:%S %p')}")
                print("Now sleeping for 1620 seconds")

                # Sleep to incubate until next assay plate is ready
                time.sleep(1620)



if __name__ == "__main__":

    experiment_app = DemoAMPExperimentApplication()

    current_time = datetime.datetime.now()

    with experiment_app.manage_experiment(
        run_name=f"Multi Plate AMP Experiment Run {current_time}",
        run_description=f"Run for multi plate AMP experiment, started at ~{current_time}",
    ):

        experiment_app.run_app()

