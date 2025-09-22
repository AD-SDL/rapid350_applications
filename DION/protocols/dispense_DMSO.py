"""
Generates SOLO .hso instruction file for first set of steps for substrate transfer experiment

"""
from liquidhandling import SoloSoft
from liquidhandling import DeepBlock_96VWR_75870_792_sterile


# SOLO PROTOCOL STEPS
def generate_hso_file(
        payload,
        temp_file_path,
):
    """generate_hso_file

    Description:
         Dispenses DMSO into dilution column wells of a substrate replicate plate using SOLO liquid handler.

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

    dmso_stock_location = "Position4"  # Location of the DMSO stock plate
    dmso_stock_column = 1  # Column in the substrate stock plate containing DMSO
    dmso_uL_volumes = [0, 0, 136.7, 136.7, 136.7, 136.7, 136.7, 200]  # DMSO volumes for each well in column 1

    # TODO: Are these volumes correct?

    dilution_plate_location = "Position3"  # Location of the dilution plate
    dilution_column = 1  # Column in the dilution plate to dispense DMSO

    rows = ["A", "B", "C", "D", "E", "F", "G", "H"]  # Rows in the dilution plate

    # ACTIONS
    # 1. Dispense DMSO into each well of dilution column with single channel transfers

    # TODO: what is the DMSO source well? Right now I'm assuming a deepwell plate with all column 1 filled with DMSO

    soloSoft.getTip("Position5", num_tips=1)  # same tip for all transfers
    for i in range(len(dmso_uL_volumes)):
        if dmso_uL_volumes[i] > 0:
            if dmso_uL_volumes[i] > 180:
                # do two transfers of half the volume, same tip for both transfers
                # Note: this is a workaround for the 180 uL tip box limitation
                transfer_volume = dmso_uL_volumes[i] / 2
                for j in range(2):
                    # TODO: Are we aspirating from the same row each time?
                    soloSoft.aspirate(
                        position=dmso_stock_location,
                        aspirate_volumes=DeepBlock_96VWR_75870_792_sterile().setCell(
                            rows[i], dmso_stock_column, transfer_volume
                        ),
                        aspirate_shift=[0, 0, flat_bottom_z_shift],
                    )
                    soloSoft.dispense(
                        position=dilution_plate_location,
                        dispense_volumes=DeepBlock_96VWR_75870_792_sterile().setCell(
                            rows[i], dilution_column, transfer_volume
                        ),
                        dispense_shift=[0, 0, flat_bottom_z_shift],
                    )
            else:  # transfer all volume in one go
                soloSoft.aspirate(
                    position=dmso_stock_location,
                    aspirate_volumes=DeepBlock_96VWR_75870_792_sterile().setCell(
                        rows[i], dmso_stock_column, dmso_uL_volumes[i]
                    ),
                    aspirate_shift=[0, 0, flat_bottom_z_shift],
                )
                soloSoft.dispense(
                    position=dilution_plate_location,
                    dispense_volumes=DeepBlock_96VWR_75870_792_sterile().setCell(
                        rows[i], dilution_column, dmso_uL_volumes[i]
                    ),
                    dispense_shift=[0, 0, flat_bottom_z_shift],
                )

    soloSoft.shuckTip()
    soloSoft.savePipeline()
