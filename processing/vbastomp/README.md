# FAME's VBA stomping detection module

FAME module to detect anomalies making use of [VBASeismograph tool](https://github.com/kirk-sayre-work/VBASeismograph)

## Requirements

* VBASeismograph
* sigtool (clamav)
* Python's `pcodedmp` module. It will be autoinstalled when the module is loaded by FAME. You dont need to set `PCODEDMP_DIR` environmen variable in your system. You have to provide it in the `vba_stomp` module configuration.
