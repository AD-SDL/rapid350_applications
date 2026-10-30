import datetime

# from AMES_TEST_SCALEUP.exp_app_scaleup_CREATE import AMESExperimentApplication
from exp_app_scaleup_CREATE import AMESExperimentApplication

# ### DAY 1 ################################################

# SET 1 =============================

# Note: Columns must be integers
dmso_stock_columns = [1,2]  # [1,2]
dilution_plate_columns = [1,2]  # [1,2]
cell_stock_columns = [1,2]

control_compound_wells = ["A1", "B1"]  # ["A1", "B1"]
test_compound_wells = ["A2", "B2"]    # ["A2", "B2"]
control_plate_location = "Position7"
test_plate_location = "Position7"

# Note: Incubator IDs must be strings
exposure_indicator_incubator_ids = ["1","5"] 
assay_384_well_incubator_ids = [
    ["2","3","4"],
    ["6","7","8"],
]

#  Run the first two experiments
current_time = datetime.datetime.now()
experiment_app = AMESExperimentApplication()
with experiment_app.manage_experiment(
    run_name=f"AMES Experiment Run, Set 1: {current_time}",
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


# SET 2 ===================

# Note: Columns must be integers
dmso_stock_columns = [3,4]  
dilution_plate_columns = [3,4]
cell_stock_columns = [1,2]  # using a new cell stock plate...

control_compound_wells = ["C1", "D1"]  
test_compound_wells = ["C2", "D2"]   
control_plate_location = "Position7"
test_plate_location = "Position7"

# Note: Incubator IDs must be strings
exposure_indicator_incubator_ids = ["9","13"] 
assay_384_well_incubator_ids = [
    ["10","11","12"],
    ["14","15","16"],
]

#  Run the first two experiments
current_time = datetime.datetime.now()
experiment_app = AMESExperimentApplication()
with experiment_app.manage_experiment(
    run_name=f"AMES Experiment Run, Set 2: {current_time}",
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