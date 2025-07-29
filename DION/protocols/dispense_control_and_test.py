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
            "Biorad 384 well (HSP3905)",       # substrate stock plate
            "DeepBlock.96.VWR-75870-792.sterile",  # 180 uL tip box
            "DeepBlock.96.VWR-75870-792.sterile",       # substrate replicate plate
            "TipBox.180uL.Axygen-EVF-180-R-S.bluebox",       # substrate replicate plate
            "DeepBlock.96.VWR-75870-792.sterile",       # substrate replicate plate
            "Empty",       # substrate replicate plate
            "Empty",       # substrate replicate plate
        ],
    )


    control_stock_location = "Position4"  # Location of the control stock plate
    control_stock_column = 2  # Column in the control stock plate containing control compound
    control_transfer_volume = 200  # Volume of control compound to transfer into dilution column wells

    test_stock_location = "Position4"  # Location of the test stock plate
    test_stock_column = 3  # Column in the test stock plate containing test compound

    dilution_plate_location = "Position3"  # Location of the dilution plate
    dilution_column = 1  # Column in the dilution plate to dispense DMSO

    # ACTIONS
    # 1. Dispense control compound into dilution plate, well in row A
    soloSoft.getTip("Position5", num_tips=1)
    soloSoft.aspirate(
        position=control_stock_location,
        aspirate_volumes=DeepBlock_96VWR_75870_792_sterile().setColumn(
            control_stock_column, control_transfer_volume
        ),
        aspirate_shift=[0, 0, flat_bottom_z_shift],
    )
    soloSoft.dispense(
        position=dilution_plate_location,
        dispense_volumes=DeepBlock_96VWR_75870_792_sterile().setColumn(
            dilution_column, control_transfer_volume
        ),
        dispense_shift=[0, 0, flat_bottom_z_shift],
    )
    soloSoft.shuckTip()

    # 2. Dispense test compound into dilution plate, well in rows B-G (H is the DMSO negative control)
    for i in range(6):






    # for i in range(len(dmso_uL_volumes)):

        # TODO: maybe take out redundant tip shucking

        # if dmso_uL_volumes[i] > 0:
        #     if dmso_uL_volumes[i] > 180:
        #         # do two transfers of half the volume, same tip for both transfers
        #         # Note: this is a workaround for the 180 uL tip box limitation
        #         transfer_volume = dmso_uL_volumes[i] / 2
        #         soloSoft.getTip("Position5", num_tips=1)
        #         for i in range(2):
        #             soloSoft.aspirate(
        #                 position=dmso_stock_location,
        #                 aspirate_volumes=DeepBlock_96VWR_75870_792_sterile().setColumn(
        #                     dmso_stock_column, transfer_volume
        #                 ),
        #                 aspirate_shift=[0, 0, flat_bottom_z_shift],
        #             )
        #             soloSoft.dispense(
        #                 position=dilution_plate_location,
        #                 dispense_volumes=DeepBlock_96VWR_75870_792_sterile().setColumn(
        #                     dilution_column, transfer_volume
        #                 ),
        #                 dispense_shift=[0, 0, flat_bottom_z_shift],
        #             )
        #         soloSoft.shuckTip()
        #     else:  # transfer all volume in one go
        #         soloSoft.getTip("Position5", num_tips=1)
        #         soloSoft.aspirate(
        #             position=dmso_stock_location,
        #             aspirate_volumes=DeepBlock_96VWR_75870_792_sterile().setColumn(
        #                 dmso_stock_column, dmso_uL_volumes[i]
        #             ),
        #             aspirate_shift=[0, 0, flat_bottom_z_shift],
        #         )
        #         soloSoft.dispense(
        #             position=dilution_plate_location,
        #             dispense_volumes=DeepBlock_96VWR_75870_792_sterile().setColumn(
        #                 dilution_column, dmso_uL_volumes[i]
        #             ),
        #             dispense_shift=[0, 0, flat_bottom_z_shift],
        #         )
        #         soloSoft.shuckTip()


    soloSoft.savePipeline()
