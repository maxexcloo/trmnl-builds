# Paper S3 Patches

`0001-native-waveform.patch` removes TRMNL's shared greyscale waveform override
from the separate Paper S3 **Patched** variant. FastEPD then uses its native
panel waveform. Original firmware is unchanged.

The patch targets the source context used by upstream v1.8.17. Other releases
must pass `git apply --check`; a mismatch fails only the patched variant.
The contrast improvement still needs verification on hardware.
