"""
Generates SOLO .hso instruction file.

"""
from liquidhandling import SoloSoft
from liquidhandling import PlateDefinition

# TODO: edit z height for deepwell, not flat bottom
# TODO: Custom plate def for 48 deepwell
# TODO: Clean up and document


### helper plate definition class
class Plate_48well_deepwell(PlateDefinition):
    def __new__(cls, plate=None):
        return PlateDefinition(
            name="48well_deepwell",
            plate=plate,
            plate_height=44.1,
            well_depth=39.7,
            rows=16,
            columns=6,
            x_offset=4.5,
            y_offset=0,
            row_spacing=9,
            column_spacing=18,
            comments="Deep 48-well plate",
        )



# SOLO PROTOCOL STEPS
def generate_hso_file(
        payload,
        temp_file_path,
):
    """generate_hso_file

    Description:
         Dispenses contents of exposure wells into indicator wells.

    Args:
        payload (dict): input variables from the wei workflow (not used in demo)
        temp_file_path (str): file path to temporarily save hso file to
    """

# * Other program variables
    # general SOLO variables
    flat_bottom_z_shift = 2  # Note: 1 is not high enough (tested)

    # * Initialize soloSoft deck layout
    soloSoft = SoloSoft(
        filename=temp_file_path,
        plateList=[
            "48well_deepwell",
            "Biorad_384_well_HSP3905",       # assay plate
            "DeepBlock.96.VWR-75870-792.sterile",  # dilution plate
            "DeepBlock.96.VWR-75870-792.sterile",       # stock plate: DMSO, control, and test compounds
            "TipBox.180uL.Axygen-EVF-180-R-S.bluebox",       # 180uL tip box
            "DeepBlock.96.VWR-75870-792.sterile",       # cells stock plate
            "Empty",
            "Empty",
        ],
    )

    # exposure/indiacator plate details
    exposure_indiacator_plate_location = "Position1"
    exposure_columns = [1,2,3]
    indicator_columns = [4,5,6]
    total_transfer_volume = 240
    half_total_transfer_volume = total_transfer_volume / 2
    # NOTE: want to transfer total volume (250uL) but can't with robots
    # TODO: check that 240 is good, how much could we transfer? <- TEST

    # mix variables
    mix_cycles = 10
    mix_volume = 80

    # ACTIONS
    # 1. Dispense all contents of exposure columns (1,2, and 3) into each well of indicator columns (1,2, and 3)
    soloSoft.getTip("Position5")  # 8-channel transfer, same tips for all transfers
    for i in range(3): # three destination columns (1,2,3)
        for j in range(2):  # two transfers needed, 1ul each time
            soloSoft.aspirate(
                position=exposure_indiacator_plate_location,
                aspirate_volumes=Plate_48well_deepwell().setColumn(
                    exposure_columns[i], half_total_transfer_volume
                ),
                aspirate_shift=[0, 0, flat_bottom_z_shift],
                mix_at_start = True,
                mix_cycles = mix_cycles,
                mix_volume = mix_volume,
                dispense_height = flat_bottom_z_shift,
            )
            soloSoft.dispense(
                position=exposure_indiacator_plate_location,
                dispense_volumes=Plate_48well_deepwell().setColumn(
                    indicator_columns[i], half_total_transfer_volume
                ),
                dispense_shift=[0, 0, flat_bottom_z_shift],
                mix_at_finish = True,
                mix_cycles = mix_cycles,
                mix_volume = mix_volume,
                aspirate_height = flat_bottom_z_shift,
            )
    soloSoft.shuckTip()

    soloSoft.savePipeline()
