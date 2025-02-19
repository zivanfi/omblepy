# omblepy
Cli tool to read records from Omron Bluetooth-LE measurement instruments


## Windows setup
First install latest python 3.x release.
Use the <a href="https://www.python.org/downloads/">official installer</a> and enable the "add to path option" in the installer. <br>
Then install the required libraries by opening a console window and executing the two commands:
| command  | library name | tested with library version |module use |
| -- | -- | -- | -- |
| `pip install bleak` | <a href="https://pypi.org/project/bleak/">bleak</a> | v0.18.1 | bluetooth-le communication |
| `pip install terminaltables` | <a href="https://pypi.org/project/terminaltables/">terminaltables</a> | v3.1.1 | formated command line output table for scanned devices |

## Linux setup
Install python ( >= version 3.8) and the two required libraries:
```
apt install python3.10
pip3 install bleak
pip3 install terminaltables
```

## Usage
For the first time pairing process you need to use the -p flag and enable pairing mode by holding the bluetooth button until you see the blinking -P- in the display:
```
python3 ./omblepy.py -p -d HEM-7322T 
```
After the first connection the -p flag can be omitted, even when executing omblepy on a different device:
```
python3 ./omblepy.py -d HEM-7322T
```
### Pairing for UBPM
If you preform this pairing for <a href="https://codeberg.org/LazyT/ubpm/">ubpm</a>, just use one of the supported devices (e.g. `-d HEM-7322T`), even if your device model is different. As far as I know the pairing process is simmilar for all omron devices. If you use an unsupported device it is expected that the pairing will work and that the -P- on the display of the omron device will change to a small square. But the tool will crash futher in the readout, because the data format / readout commands for the stored records are different. Nevertheless your omron device is now bound to the mac address of your pc and ubpm should work without mac address spoofing. <br>
If you see the message "Could not enter key programming mode." or "Failure to programm new key." the pairing procedure did NOT work. Please see the troubleshooting section and if the problem persists please open an issue. <br>
Success is indicated by the message "Paired device successfully with new key".

### Flags table
| flag  | alternative long flag  | always required | required on first connection | description | usage example | 
| ----- | ----- | ----- | ----- | ----- | ----- |
| `-h`  | `--help` | - | - | display help for all possible flags, similar to this table | `python3 ./omblepy.py -h` |
| `-d`  | `--device` |✔️ | ✔️ | select which device libary will be loaded | `python3 ./omblepy.py -d HEM-7322T` |
| `-p`  | `--pair` | ❌ | ✔️ | use to write pairing key on first connection with this pc | `python3 ./omblepy.py -d HEM-7322T -p` |
| `-m`  | `--mac` |❌ | ❌ | select omron devices mac and skip bluetooth scan and device selection dialog | `python3 ./omblepy.py -d HEM-7322T -m 11:22:33:44:55:66` |
| `-n`  | `--newRecOnly` | ❌ | ❌ | instead of downloading all records, check and update the "new records couter" and only transfer new records | `python3 ./omblepy.py -d HEM-7322T -n` |
| `-t`  | `--timeSync` | ❌ | ❌ | synchronize omron internal clock with system time | `python3 ./omblepy.py -d HEM-7322T -t` |
|  |`--loggerDebug`  | ❌ | ❌ | displays every ingoing and outgoing data for debugging purposes | `python3 ./omblepy.py -d HEM-7322T --loggerDebug` |

## omron device support matrix
| device model |typical name |  pairing | basic data readout | new record counter | time sync | contributors / testers / help by | 
| ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| [HEM-7322T](deviceSpecific/hem-7322t.py) | M700 Intelli IT | ✔️ | ✔️ | ✔️ | ✔️ | userx14 |
| [HEM-7361T](deviceSpecific/hem-7361t.py)  | M500 Intelli IT | ✔️ | ❓️ | ❓️ | ❓ | LazyT, userx14 |
| [HEM-7600T](deviceSpecific/hem-7600t.py) | Omron Evolv | ✔️ | ✔️ | ✔️ | ✔️ | vulcainman |

✔️=tested working, ❓=not tested , ❌=not supported yet <br>

Please open an issue if you can test a feature or an currently unsupported device.

## Troubleshooting
- Remove the pairing with the omron device using your os bluetooth dialog.
- Try a different pc / os if the pairing does not work.
  - On the devices I used to test win10 did always work, while ubuntu didn't work on some versions.
- If the pairing works and there is an error in the readout use the `--loggerDebug` flag and please open an issue.
- Windows specific
  - Do not use the CSR harmony stack (CSR 8510 based usb dongles), it is incompatible.
- Linux specific
  - Preferably test on a device with only one bluetooth adapter connected.
  - Restart the bluetooth stack `sudo systemctl restart bluetooth`.
  - Delete the bluetooth adapter cache with `sudo rm -r /var/lib/bluetooth/$yourBtCardMacAddress`.
  - If you have two bluetooth adapters in your system, open a second terminal alongside omblepy and use `bluetoothctl` to confirm pairing dialogs by typing `yes` when promped, some graphical interfaces will not show the pairing dialog for the second adapter.
  - When you are on ubuntu, install blueman, since it seems to be designed with multiple adapters in mind.
  - Try other versions of bluez, for me versions around bluez 5.55 worked best.


## Documentation 

### Packet format
Example message sent to request a read of 0x26 bytes starting from address 0x0260:
messagelength | command type      | start address | readsize | padding     | crc with xor
---           | ---               | ---           | ---      | ---         | ---
10            | 80 00             | 02 60         | 26       | 00          | 4d
in bytes      | read from address | in bytes      | in bytes | 1byte zero  | all bytes xored = zero


## Related Projects
A huge thank you goes to LazyT and his <a href=https://codeberg.org/LazyT/ubpm>UBPM project</a>
which provided extremely usefull insight how the reception with multiple bluetooth channels works.
