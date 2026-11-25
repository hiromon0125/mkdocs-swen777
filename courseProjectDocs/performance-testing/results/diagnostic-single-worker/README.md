# Excluded single-worker diagnostic

The initial full stress run used one Locust worker inside the two-CPU generator container. Its log warned that worker CPU exceeded 90%; the generator process-tree trace peaked at 105.9% of one CPU. A single Python worker could therefore constrain the offered workload despite a two-CPU container allowance.

The initial campaign was stopped, and final measurements use two Locust workers plus a master inside the same generator container. These diagnostic files are retained to explain that change and are **excluded from all final campaign metrics and findings**. The earlier partially executed campaign is not one of the three final repetitions.

The `metadata.json` describes the old single-worker implementation. See the final `baseline-*-*/metadata.json` files for the measured two-worker configuration and the campaign suite manifest for its source hashes and image ID.
