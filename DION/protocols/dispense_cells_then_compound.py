"""
Generates SOLO .hso instruction file.

"""
from liquidhandling import SoloSoft
from liquidhandling import DeepBlock_96VWR_75870_792_sterile

# TODO: edit z height for deepwell, not flat bottom
# TODO: Recalibrate SOLO position 1, pipette hitting side of deepwell when dispensing
# TODO: do I need to define a new plate type in liquidhandling for 48 deepwell? !!!!!!!

# SOLO PROTOCOL STEPS
def generate_hso_file(
        payload,
        temp_file_path,
):
    """generate_hso_file

    Description:
         Dispenses cells from cell stock plate into exposure wells using SOLO liquid handler.

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
            "48well_deepwell",  # exposure/indicator plate
            "Biorad 384 well (HSP3905)",       # assay plate
            "DeepBlock.96.VWR-75870-792.sterile",  # dilution plate
            "DeepBlock.96.VWR-75870-792.sterile",       # stock plate: DMSO, control, and test compounds
            "TipBox.180uL.Axygen-EVF-180-R-S.bluebox",       # 180uL tip box
            "DeepBlock.96.VWR-75870-792.sterile",       # cells stock plate
            "Empty",
            "Empty",
        ],
    )

    # stock cells plate details
    cells_stock_location = "Position6"
    cells_stock_column = 1    # Cell stock needs to be in each well of column 1, at least 800uL+ per well
    cells_transfer_volume = 240  # will need to do two transfers
    half_cells_transfer_volume = cells_transfer_volume / 2

    # exposure/indiacator plate details
    exposure_indiacator_plate_location = "Position1"

    # compound serial dilutuon plate details
    dilution_plate_location = "Position3"  # Location of the dilution plate
    dilution_column = 1  # Column in the dilution plate to dispense DMSO
    dilution_transfer_volume = 10   # 10uL

    # mix variables
    mix_cycles = 10
    mix_volume = 150

    # ACTIONS
    # 1. Dispense 240 ul cells into each well of exposure columns 1,2, and 3
    soloSoft.getTip("Position5")  # 8-channel transfer, same tips for all transfers
    for i in range(3): # three destination columns (1,2,3)
        for j in range(2):  # two transfers needed, 120ul each time
            soloSoft.aspirate(
                position=cells_stock_location,
                aspirate_volumes=DeepBlock_96VWR_75870_792_sterile().setColumn(
                    cells_stock_column, half_cells_transfer_volume
                ),
                aspirate_shift=[0, 0, flat_bottom_z_shift],
                mix_at_start = True,
                mix_cycles = mix_cycles,
                mix_volume = mix_volume,
                dispense_height = flat_bottom_z_shift
            )
            soloSoft.dispense(
                position=exposure_indiacator_plate_location,
                dispense_volumes=DeepBlock_96VWR_75870_792_sterile().setColumn(
                    (i + 1) , half_cells_transfer_volume
                ),
                dispense_shift=[0, 0, flat_bottom_z_shift],
            )

    # 2. dispense 10ul serial diluted compound into exposure columns 1, 2, and 3
    for i in range(3):
        soloSoft.getTip("Position5")
        soloSoft.aspirate(
            position=dilution_plate_location,
            aspirate_volumes=DeepBlock_96VWR_75870_792_sterile().setColumn(
                dilution_column, dilution_transfer_volume
            ),
            aspirate_shift=[0, 0, flat_bottom_z_shift],
            mix_at_start = True,
            mix_cycles = mix_cycles,
            mix_volume = mix_volume,
            dispense_height = flat_bottom_z_shift
        )
        soloSoft.dispense(
            position=exposure_indiacator_plate_location,
            dispense_volumes=DeepBlock_96VWR_75870_792_sterile().setColumn(
                (i + 1), dilution_transfer_volume
            ),
            dispense_shift=[0, 0, flat_bottom_z_shift],
            mix_at_finish = True,
            mix_cycles = mix_cycles,
            mix_volume = mix_volume,
            aspirate_height = flat_bottom_z_shift,
        )

    soloSoft.shuckTip()
    soloSoft.savePipeline()
