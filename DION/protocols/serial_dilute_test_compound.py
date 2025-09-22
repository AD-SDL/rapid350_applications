"""
Generates SOLO .hso instruction file for first set of steps for substrate transfer experiment

"""
from liquidhandling import SoloSoft
from liquidhandling import DeepBlock_96VWR_75870_792_sterile


# TODO: Should I be getting a new tip for each transfer?


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
            "Biorad 384 well (HSP3905)",       # assay plate
            "DeepBlock.96.VWR-75870-792.sterile",  # dilution plate
            "DeepBlock.96.VWR-75870-792.sterile",       # stock plate: DMSO, control, and test compounds
            "TipBox.180uL.Axygen-EVF-180-R-S.bluebox",       # 180uL tip box
            "DeepBlock.96.VWR-75870-792.sterile",       # cells stock plate
            "Empty",
            "Empty",
        ],
    )

    dilution_plate_location = "Position3"  # Location of the dilution plate
    dilution_column = 1  # Column in the dilution plate to dispense DMSO
    serial_transfer_volume = 63.3

    mix_volume = 150
    num_mixes = 5

    rows = ["A", "B", "C", "D", "E", "F", "G", "H"]  # Rows in the dilution plate

    # ACTIONS
    # serial dilute test compond into dilution plate, wells in row B->G, using same tip, and mix
    soloSoft.getTip("Position5", num_tips=1)
    for i in range(1, 6):
        soloSoft.aspirate(
            position=dilution_plate_location,
            aspirate_volumes=DeepBlock_96VWR_75870_792_sterile().setCell(
                rows[i], dilution_column, serial_transfer_volume
            ),
            aspirate_shift=[0, 0, flat_bottom_z_shift],
            mix_at_start= True,
            mix_cycles=num_mixes,
            mix_volume=mix_volume,
            dispense_height = flat_bottom_z_shift
        )
        soloSoft.dispense(
            position=dilution_plate_location,
            dispense_volumes=DeepBlock_96VWR_75870_792_sterile().setCell(
                rows[i + 1], dilution_column, serial_transfer_volume
            ),
            dispense_shift=[0, 0, flat_bottom_z_shift],
        )
    soloSoft.shuckTip()

    soloSoft.savePipeline()
