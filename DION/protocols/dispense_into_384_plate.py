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
    # variables
    transfer_volume = 50
    mix_volume_at_start = 50
    # mix_volume_at_end = 50
    mix_cycles = 5
    exposure_indiacator_plate_location = "Position1"


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

    # ACTIONS -------------
        # TODO: are we ok with using only two tips for all transfers? one tip for each half of plate?

    current_indicator_column = payload["current_indicator_column"]
    half = payload["half"]  # 'A' or 'B' half of the 96 well plate

     # pick up tip
    soloSoft.getTip("Position5")

    plate = Plate_384_Corning_3540_BlackwClearBottomAssay()
    print(f"plate.columns: {plate.columns}")

    # aspirate and dispense into one half of the 384 well plate
    # Note: SoloSoft will crash if too many steps are included in one file
    if half == 1:
        for i in range(1,13):  # first half of the 384 well plate
            # aspirate 100uL from indicator plate column
            soloSoft.aspirate(
                position=exposure_indiacator_plate_location,
                aspirate_volumes=DeepBlock_96VWR_75870_792_sterile().setColumn(
                    current_indicator_column, transfer_volume * 2
                ),
                aspirate_shift=[0, 0, 2],  # flat bottom z shift (# TODO: should this be different for deepwell?)
                mix_at_start=True,
                mix_cycles=mix_cycles,
                mix_volume=mix_volume_at_start,
                dispense_height = 2,  # make sure correct here...
            )

            # dipsense 50uL into each well rows (A,C,E,G,I,K,M,O) of 384 well plate column i
            soloSoft.dispense(
                position="Position2",
                dispense_volumes=Plate_384_Corning_3540_BlackwClearBottomAssay().setColumn(
                    i, transfer_volume
                ),
                dispense_shift=[0, 0, 2],
            )

            # dispense 50uL into each well rows (B,D,F,H,J,L,N,P) of 384 well plate column i
            dispense_volumes_startB = Plate_384_Corning_3540_BlackwClearBottomAssay().setColumn(
                i, transfer_volume
            )
            # edit dispense volumes to start at Row B
            dispense_volumes_startB[0][i-1] = 0

            soloSoft.dispense(
                position="Position2",
                dispense_volumes=dispense_volumes_startB,
                dispense_shift=[0, 0, 2]
            )

    elif half == 2:
        for i in range(13,25,2):  # there are 24 columns in 384 well plate,
            # aspirate 100uL from indicator plate column
            soloSoft.aspirate(
                position=exposure_indiacator_plate_location,
                aspirate_volumes=DeepBlock_96VWR_75870_792_sterile().setColumn(
                    current_indicator_column, transfer_volume * 4
                ),
                aspirate_shift=[0, 0, 2],  # flat bottom z shift (# TODO: should this be different for deepwell?)
                mix_at_start=True,
                mix_cycles=mix_cycles,
                mix_volume=mix_volume_at_start,
                dispense_height = 2,  # make sure correct here...
            )

            # dipsense 50uL into each well rows (A,C,E,G,I,K,M,O) of 384 well plate column i
            soloSoft.dispense(
                position="Position2",
                dispense_volumes=Plate_384_Corning_3540_BlackwClearBottomAssay().setColumn(
                    i, transfer_volume
                ),
                dispense_shift=[0, 0, 2],
            )

            # dispense 50uL into each well rows (B,D,F,H,J,L,N,P) of 384 well plate column i
            dispense_volumes_startB = Plate_384_Corning_3540_BlackwClearBottomAssay().setColumn(
                i, transfer_volume
            )
            # edit dispense volumes to start at Row B
            dispense_volumes_startB[0][i-1] = 0

            soloSoft.dispense(
                position="Position2",
                dispense_volumes=dispense_volumes_startB,
                dispense_shift=[0, 0, 2]
            )



    soloSoft.shuckTip()
    soloSoft.savePipeline()


