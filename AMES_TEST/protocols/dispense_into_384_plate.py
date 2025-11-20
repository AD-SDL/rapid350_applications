"""
Generates SOLO .hso instruction file.
"""
from liquidhandling import SoloSoft
from liquidhandling import Plate_384_Corning_3540_BlackwClearBottomAssay, DeepBlock_96VWR_75870_792_sterile


# SOLO PROTOCOL STEPS
def generate_hso_file(
        payload,
        temp_file_path,
):
    """generate_hso_file

    Description:
        Dispenses 50uL from each well in a 96 well plate into a 384 well plate,
        dispensing into every other well (i.e. A1, A3, A5...B1, B3, B5... etc)

    Args:
        payload (dict): input variables from the wei workflow (not used in demo)
        temp_file_path (str): file path to temporarily save hso file to
    """
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

    # variables
    z_shift = 2
    transfer_volume = 50
    mix_volume_at_start = 50
    mix_cycles = 5
    exposure_indicator_plate_location = "Position1"

    current_indicator_column = payload["current_indicator_column"]
    half = payload["half"]  # 'A' or 'B' half of the 96 well plate
    plate = Plate_384_Corning_3540_BlackwClearBottomAssay()

    # ACTIONS
    soloSoft.getTip("Position5")

    # 1. Aspirate and dispense into first half of the 384 well plate
    # NOTE: SoloSoft will crash if too many steps are included in one file
    if half == 1:
        for i in range(1,13):  # first half of the 384 well plate
            # 1a. Aspirate 100uL from indicator plate column
            soloSoft.aspirate(
                position=exposure_indicator_plate_location,
                aspirate_volumes=DeepBlock_96VWR_75870_792_sterile().setColumn(
                    current_indicator_column, transfer_volume * 2
                ),
                aspirate_shift=[0, 0, z_shift],  # flat bottom z shift works here
                mix_at_start=True,
                mix_cycles=mix_cycles,
                mix_volume=mix_volume_at_start,
                dispense_height = z_shift,
            )

            # 1b. Dispense 50uL into each well rows (A,C,E,G,I,K,M,O) of 384 well plate column i
            soloSoft.dispense(
                position="Position2",
                dispense_volumes=Plate_384_Corning_3540_BlackwClearBottomAssay().setColumn(
                    i, transfer_volume
                ),
                dispense_shift=[0, 0, z_shift],
            )

            # 1c. Dispense 50uL into each well rows (B,D,F,H,J,L,N,P) of 384 well plate column i
            dispense_volumes_startB = Plate_384_Corning_3540_BlackwClearBottomAssay().setColumn(
                i, transfer_volume
            )
            dispense_volumes_startB[0][i-1] = 0  # edit dispense volumes to start at Row B
            soloSoft.dispense(
                position="Position2",
                dispense_volumes=dispense_volumes_startB,
                dispense_shift=[0, 0, 2]
            )

    # 2. Aspirate and dispense into second half of the 384 well plate
    elif half == 2:
        for i in range(13,25,2):  # there are 24 columns in 384 well plate,
            # 2a. Aspirate 100uL from indicator plate column
            soloSoft.aspirate(
                position=exposure_indicator_plate_location,
                aspirate_volumes=DeepBlock_96VWR_75870_792_sterile().setColumn(
                    current_indicator_column, transfer_volume * 2
                ),
                aspirate_shift=[0, 0, z_shift],  
                mix_at_start=True,
                mix_cycles=mix_cycles,
                mix_volume=mix_volume_at_start,
                dispense_height = z_shift,
            )

            # 2b. Dispense 50uL into each well rows (A,C,E,G,I,K,M,O) of 384 well plate column i
            soloSoft.dispense(
                position="Position2",
                dispense_volumes=Plate_384_Corning_3540_BlackwClearBottomAssay().setColumn(
                    i, transfer_volume
                ),
                dispense_shift=[0, 0, 2],
            )

            # 2c. Dispense 50uL into each well rows (B,D,F,H,J,L,N,P) of 384 well plate column i
            dispense_volumes_startB = Plate_384_Corning_3540_BlackwClearBottomAssay().setColumn(
                i, transfer_volume
            )
            dispense_volumes_startB[0][i-1] = 0  # edit dispense volumes to start at Row B
            soloSoft.dispense(
                position="Position2",
                dispense_volumes=dispense_volumes_startB,
                dispense_shift=[0, 0, 2]
            )

    soloSoft.shuckTip()
    soloSoft.savePipeline()


