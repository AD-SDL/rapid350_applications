import datetime

# from AMES_TEST_SCALEUP.exp_app_scaleup_CREATE import AMESExperimentApplication
from exp_app_scaleup_CREATE import AMESExperimentApplication

### DAY 2 ################################################################

# SET 3 ==========================

# Note: Columns must be integers
dmso_stock_columns = [1,2]   # got a new plate for second day
dilution_plate_columns = [1,2]  # got a new plate for second day
cell_stock_columns = [1,2]  # got a new plate for second day

control_compound_wells = ["E1", "F1"]  
test_compound_wells = ["E2", "F2"]    
control_plate_location = "Position7"
test_plate_location = "Position7"

# Note: Incubator IDs must be strings
exposure_indicator_incubator_ids = ["17","21"] 
assay_384_well_incubator_ids = [
    ["18","19","20"],
    ["22","23","24"],
]

#  Run the first two experiments
current_time = datetime.datetime.now()
experiment_app = AMESExperimentApplication()
with experiment_app.manage_experiment(
    run_name=f"AMES Experiment Run, Set 3: {current_time}",
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


# SET 4 ======================

# Note: Columns must be integers
dmso_stock_columns = [3,4]  
dilution_plate_columns = [3,4]
cell_stock_columns = [1,2]  # using a new cell stock plate...

control_compound_wells = ["G1", "H1"]  
test_compound_wells = ["G2", "H2"]   
control_plate_location = "Position7"
test_plate_location = "Position7"

# Note: Incubator IDs must be strings
exposure_indicator_incubator_ids = ["25","29"] 
assay_384_well_incubator_ids = [
    ["26","27","28"],
    ["30","31","32"],
]

#  Run the first two experiments
current_time = datetime.datetime.now()
experiment_app = AMESExperimentApplication()
with experiment_app.manage_experiment(
    run_name=f"AMES Experiment Run, Set 4: {current_time}",
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