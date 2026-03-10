"""
Generates SOLO .hso instruction file for first set of steps for substrate transfer experiment

"""
import os
import sys
import time
import argparse
from liquidhandling import SoloSoft
from liquidhandling import Reservoir_12col_Agilent_201256_100_BATSgroup, Plate_96_Corning_3635_ClearUVAssay, DeepBlock_96VWR_75870_792_sterile

# TODO: THIS MIGHT HAVE TOO MANY STEPS, CHECK THIS

# SOLO PROTOCOL STEPS    
def generate_hso_file(
        payload, 
        temp_file_path,
): 
    """generate_hso_file

    Description: 
        Generates a SOLOSoft .hso file

        Steps: 
            - Aspirate 150uL volume from column 1 on flat-bottom plate in SOLO Position 2
            - Dispense 150uL into column 12 on flat-bottom plate in SOLO Position 2

    Args:
        payload (dict): input variables from the wei workflow
        temp_file_path (str): file path to temporarily save hso file to 
    """

# * Other program variables
    # general SOLO variables
    blowoff_volume = 10
    num_mixes = 3
    media_z_shift = 0.5
    reservoir_z_shift = 0.5  # z shift for deep blocks (Deck Positions 3 and 5)
    flat_bottom_z_shift = 2  # Note: 1 is not high enough (tested)

    # protocol specific variables
    substrate_transfer_volume = 150

    """
    SOLO STEP 1: TRANSFER SUBSTRATE STOCK INTO REPLICATE PLATES 1 AND 2  -----------------------------------------------------------------
    """
    # * Initialize soloSoft deck layout 
    soloSoft = SoloSoft(
        filename=temp_file_path,
        plateList=[
            "Plate.96.Corning-3635.ClearUVAssay",
            "Plate.96.Corning-3635.ClearUVAssay",       # substrate stock plate
            "TipBox.180uL.Axygen-EVF-180-R-S.bluebox",  # 180 uL tip box
            "Plate.96.Corning-3635.ClearUVAssay",       # substrate replicate plate
            "Plate.96.Corning-3635.ClearUVAssay",       # substrate replicate plate
            "Plate.96.Corning-3635.ClearUVAssay",       # substrate replicate plate
            "Plate.96.Corning-3635.ClearUVAssay",       # substrate replicate plate
            "Plate.96.Corning-3635.ClearUVAssay",       # substrate replicate plate
        ],
    )

    # * First set of 12 substrate column transfers (Stock plate column 1 --> replicate plate in position 4)
    soloSoft.getTip("Position3")  

    soloSoft.aspirate(
        position="Position2",
        aspirate_volumes=Plate_96_Corning_3635_ClearUVAssay().setColumn(
            1, substrate_transfer_volume
        ),
        aspirate_shift=[0, 0, flat_bottom_z_shift],
    )
    soloSoft.dispense(
        position="Position2",
        dispense_volumes=Plate_96_Corning_3635_ClearUVAssay().setColumn(
            12, substrate_transfer_volume
        ),
        dispense_shift=[0, 0, flat_bottom_z_shift],
    )

    
    # * Dispense tips at end of protocol and process these instructions into a .hso file 
    soloSoft.shuckTip()
    soloSoft.savePipeline()
    


