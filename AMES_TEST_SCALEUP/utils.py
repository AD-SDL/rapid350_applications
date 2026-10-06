import csv
import os
from datetime import datetime


def log_assay_plate_incubation(
    microplate_id,
    incubation_start_time,
    csv_path="assay_plate_incubation_log.csv",
):
    """Append one assay plate incubation event to a CSV."""

    file_exists = os.path.isfile(csv_path)

    readable_time = datetime.fromtimestamp(
        incubation_start_time
    ).isoformat(timespec="seconds")

    with open(csv_path, mode="a", newline="") as csv_file:
        writer = csv.writer(csv_file)

        if not file_exists:
            writer.writerow([
                "microplate_id",
                "incubation_start_time",
                "unix_timestamp",
            ])

        writer.writerow([
            microplate_id,
            readable_time,
            int(incubation_start_time),
        ])