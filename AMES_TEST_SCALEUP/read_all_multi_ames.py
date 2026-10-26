import csv
import time

import datetime
from exp_app_scaleup_READ import ReadAmesExperimentApplication

FILE_PATH = "assay_plate_incubation_log.csv"

# How long the plate must incubate before being read.

# INCUBATION_SECONDS = 600  # 10 minutes for TESTING!

INCUBATION_SECONDS = 172800  # 172800 = 48 hours

# How often to check for new/updated plates
CHECK_INTERVAL_SECONDS = 3 * 60


def read_plates():
    """Open and read the current CSV contents."""
    with open(FILE_PATH, "r", newline="") as f:
        return list(csv.DictReader(f))


def update_plate_complete(plate_id):
    """
    Immediately open the CSV, mark the specified plate as complete,
    then close the file so the change is visible to other programs.
    """

    # Open and read the current version of the file
    with open(FILE_PATH, "r", newline="") as f:
        reader = csv.DictReader(f)
        plates = list(reader)
        fieldnames = reader.fieldnames

    # Mark the specified plate as complete
    for plate in plates:
        if plate["microplate_id"] == str(plate_id):
            plate["complete"] = "true"
            break

    # Open, write, and close the file immediately
    with open(FILE_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(plates)


def read_plate(plate):
    """
    Put your actual plate-reading code here.

    Return True when the plate was successfully read.
    Return False if the reading failed.
    """

    plate_id = plate["microplate_id"]

    print(f"Reading plate {plate_id}...")

    # Run the experiment application to read one assay plate in the hidex
    current_time = datetime.datetime.now()
    experiment_app = ReadAmesExperimentApplication()
    with experiment_app.manage_experiment(
        run_name=f"Ames READ PLATE Experiment App {current_time}",
        run_description=f"Run for AMES Test LDRD experiment, started at ~{current_time}",
    ):
        experiment_app.run_app(
           microplate_id = plate_id
        )
    # --------------------------------------------------
    # YOUR PLATE READING CODE GOES HERE
    # --------------------------------------------------

    # For now, pretend the reading succeeded.
    return True


def main():

    print("Plate monitoring started.")

    while True:

        # Always reload the file before doing anything.
        plates = read_plates()

        # If there are no plates, wait and check again.
        if not plates:
            print("No plates found.")
            time.sleep(CHECK_INTERVAL_SECONDS)
            continue

        found_ready_plate = False

        # Look for a plate that needs to be read
        for plate in plates:

            # Skip plates that have already been completed
            if plate.get("complete", "").lower() == "true":
                continue

            plate_id = plate["microplate_id"]
            timestamp = int(plate["unix_timestamp"])

            # Calculate how long the plate has been incubating
            elapsed = time.time() - timestamp

            # Check whether the required incubation time has passed
            if elapsed >= INCUBATION_SECONDS:

                found_ready_plate = True

                print(
                    f"Plate {plate_id} is ready "
                    f"({elapsed / 60:.1f} minutes elapsed)."
                )

                # --------------------------------------------------
                # READ THE PLATE
                # --------------------------------------------------

                success = read_plate(plate)

                # --------------------------------------------------
                # IMMEDIATELY UPDATE THE CSV
                # --------------------------------------------------

                if success:
                    update_plate_complete(plate_id)

                    print(
                        f"Plate {plate_id} complete. "
                        f"CSV updated."
                    )

                else:
                    print(
                        f"Plate {plate_id} failed. "
                        f"It will be retried."
                    )

                # Stop processing this copy of the CSV.
                # The next loop will reload the file from disk.
                break

        # Reload the CSV after any reading so we have
        # the most current version of the file.
        plates = read_plates()

        # Check whether every plate is complete
        if plates and all(
            plate.get("complete", "").lower() == "true"
            for plate in plates
        ):
            print("COMPLETE!")
            break

        # If we just read a plate, immediately reload the file
        # rather than waiting three minutes.
        if found_ready_plate:
            continue

        # Nothing is ready yet.
        print(
            f"No plates ready. "
            f"Checking again in {CHECK_INTERVAL_SECONDS // 60} minutes..."
        )

        time.sleep(CHECK_INTERVAL_SECONDS)


   




if __name__ == "__main__":
    main()

    