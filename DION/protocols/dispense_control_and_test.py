"""
Generates SOLO .hso instruction file for first set of steps for substrate transfer experiment

"""
from liquidhandling import SoloSoft
from liquidhandling import DeepBlock_96VWR_75870_792_sterile

# TODO: should I mix?


# SOLO PROTOCOL STEPS
def generate_hso_file(
        payload,
        temp_file_path,
):
    """generate_hso_file

    Description:
         Dispenses control and test compound into dilution column wells of a substrate replicate plate using SOLO liquid handler.

    Args:
        payload (dict): input variables from the wei workflow (not used in demo)
        temp_file_path (str): file path to temporarily save hso file to
    """

# * Other program variables
    # general SOLO variables
    flat_bottom_z_shift = 2  # Note: 1 is not high enough (tested)

    """
    SOLO STEP 1: TRANSFER DMSO INTO DILUTION COLUMN WELLS -----------------------------------------------------------------
    """
    # * Initialize soloSoft deck layout
    soloSoft = SoloSoft(
        filename=temp_file_path,
        plateList=[
            "Empty",
            "Plate.384.Corning-3540.BlackwClearBottomAssay",       # assay plate
            "DeepBlock.96.VWR-75870-792.sterile",  # dilution plate
            "DeepBlock.96.VWR-75870-792.sterile",       # stock plate: DMSO, control, and test compounds
            "TipBox.180uL.Axygen-EVF-180-R-S.bluebox",       # 180uL tip box
            "DeepBlock.96.VWR-75870-792.sterile",       # cells stock plate
            "Empty",
            "Empty",
        ],
    )


    control_stock_location = "Position4"  # Location of the control stock plate
    control_stock_row = "A"  # Row in the control stock plate containing control compound
    control_stock_column = 2  # Column in the control stock plate containing control compound
    control_transfer_volume = 200  # Volume of control compound to transfer into dilution column wells

    test_stock_location = "Position4"  # Location of the test stock plate
    test_stock_row = "B"  # Row in the test stock plate containing test compound
    test_stock_column = 3  # Column in the test stock plate containing test compound
    test_compound_volume = 200  # Test compound volumes for each well in column 1

    dilution_plate_location = "Position3"  # Location of the dilution plate
    dilution_column = 1  # Column in the dilution plate to dispense DMSO

    rows = ["A", "B", "C", "D", "E", "F", "G", "H"]  # Rows in the dilution plate

    # ACTIONS
    # 1. Dispense control compound into dilution plate, well in row A
    soloSoft.getTip("Position5", num_tips=1)
    soloSoft.aspirate(
        position=control_stock_location,
        aspirate_volumes=DeepBlock_96VWR_75870_792_sterile().setCell(
            control_stock_row, control_stock_column, control_transfer_volume
        ),
        aspirate_shift=[0, 0, flat_bottom_z_shift],
    )
    soloSoft.dispense(
        position=dilution_plate_location,
        dispense_volumes=DeepBlock_96VWR_75870_792_sterile().setCell(
            rows[0], dilution_column, control_transfer_volume
        ),
        dispense_shift=[0, 0, flat_bottom_z_shift],
    )
    soloSoft.shuckTip()

    # 2. Dispense test compound into dilution plate, well in row B
    soloSoft.getTip("Position5", num_tips=1)
    soloSoft.aspirate(
        position=test_stock_location,
        aspirate_volumes=DeepBlock_96VWR_75870_792_sterile().setCell(
            test_stock_row, test_stock_column, test_compound_volume
        ),
        aspirate_shift=[0, 0, flat_bottom_z_shift],
    )
    soloSoft.dispense(
        position=dilution_plate_location,
        dispense_volumes=DeepBlock_96VWR_75870_792_sterile().setCell(
            rows[1], dilution_column, test_compound_volume
        ),
        dispense_shift=[0, 0, flat_bottom_z_shift],
    )
    soloSoft.shuckTip()


    soloSoft.savePipeline()
