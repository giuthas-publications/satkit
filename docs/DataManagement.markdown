# Data Management

SATKIT aims to support clean, clear, and safe data management. The data
management model of SATKIT divides data into three different kinds of locations.
First, as seen in the diagram below, we have the copies of original data. SATKIT
should never be allowed to manipulate these. Instead, a manual local copy of
recorded data should be created by the user. 

![data management](data_management.drawio.png)

This is referred to as Recorded data in the diagram and SATKIT treats it as --
mostly -- immutable. The only files SATKIT will write into or modify in the
recorded data directories are the `satkit.yaml` and `satkit_manifest.yaml`
files. The first one contains instructions from the user to SATKIT on how to
import the data, the second one is a SATKIT generated list of all of the data
SATKIT has derived from this set of recorded data and saved elsewhere.

Finally, SATKIT Scenarios are different data runs specified each in their own
`satkit_scenario.yaml` files. These files list which derived data should be
generated and which parameters to use in the generation. To save time and
resources, SATKIT will check the `satkit_manifest.yaml` files to see if the
required data already exists before running the generation code. If the data
exists, then instead of re-generating it SATKIT will just make a local copy of
it in the Scenario directory.
