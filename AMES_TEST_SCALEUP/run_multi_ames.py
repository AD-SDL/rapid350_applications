import datetime

from exp_app_scaleup import AMESExperimentApplication



dmso_stock_columns = [5,2]  # [1,2]
dilution_plate_columns = [7,2]  # [1,2]
cell_stock_columns = [1,2]

control_compound_wells = ["C1", "D1"]  # ["A1", "B1"]
test_compound_wells = ["E2", "F2"]    # ["A2", "B2"]
control_plate_location = "Position7"
test_plate_location = "Position7"

exposure_indicator_incubator_ids = [1,5] 
assay_384_well_incubator_ids = [
    [2,3,4],
    [6,7,8],
]


#  Run the first two experiments
current_time = datetime.datetime.now()
experiment_app = AMESExperimentApplication()
with experiment_app.manage_experiment(
    run_name=f"AMES Experiment Run {current_time}",
    run_description=f"Run for AMES Test LDRD experiment, started at ~{current_time}",
):
    experiment_app.run_app(
        experiment_set = 1,
        dmso_stock_columns = dmso_stock_columns,
        dilution_plate_columns = dilution_plate_columns,
        cell_stock_columns = cell_stock_columns,
        control_compound_wells = control_compound_wells,
        control_plate_location = control_plate_location,
        test_compound_wells = test_compound_wells,
        test_plate_location = test_plate_location,
        exposure_indicator_incubator_ids = exposure_indicator_incubator_ids,
        assay_384_well_incubator_ids = assay_384_well_incubator_ids,
        
    )