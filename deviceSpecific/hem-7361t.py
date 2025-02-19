import sys
import datetime
import logging
logger = logging.getLogger("omblepy")

sys.path.append('..')
from sharedDriver import sharedDeviceDriverCode

class deviceSpecificDriver(sharedDeviceDriverCode):
    deviceEndianess                 = "little"
    userStartAdressesList           = [0x0098, 0x06D8]
    perUserRecordsCountList         = [100   , 100   ]
    recordByteSize                  = 0x10
    transmissionBlockSize           = 0x10
    
    settingsReadAddress             = 0x0010
    settingsWriteAddress            = 0x0054

    settingsUnreadRecordsBytesSlice = slice(0x00, 0x10)
    settingsTimeSyncBytesSlice      = slice(0x2C, 0x3C)
    
    def deviceSpecific_ParseRecordFormat(self, singleRecordAsByteArray):
        recordDict             = dict()
        minute                 = self._bytearrayBitsToInt(singleRecordAsByteArray, 68, 73)
        second                 = self._bytearrayBitsToInt(singleRecordAsByteArray, 74, 79)
        second                 = min([second, 59]) #for some reason the second value can range up to 63
        recordDict["mov"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 80, 80)
        recordDict["ihb"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 81, 81)
        month                  = self._bytearrayBitsToInt(singleRecordAsByteArray, 82, 85)
        day                    = self._bytearrayBitsToInt(singleRecordAsByteArray, 86, 90)
        hour                   = self._bytearrayBitsToInt(singleRecordAsByteArray, 91, 95)
        year                   = self._bytearrayBitsToInt(singleRecordAsByteArray, 98, 103) + 2000
        recordDict["bpm"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 104, 111)
        recordDict["dia"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 112, 119)
        recordDict["sys"]      = self._bytearrayBitsToInt(singleRecordAsByteArray, 120,  127) + 25
        recordDict["datetime"] = datetime.datetime(year, month, day, hour, minute, second)
        return recordDict
    
    def deviceSpecific_syncWithSystemTime(self):
        logger.warning("Sorry, time sync is not yet tested on HEM7361t. Please open an issue if you need this or can test this.")
        #untested code, enable it by removing the tripple quotation marks before and after
        """
        timeSyncSettingsCopy = self.cachedSettingsBytes[self.settingsTimeSyncBytesSlice]
        #read current time from cached settings bytes
        year, month, day, hour, minute, second = [int(byte) for byte in timeSyncSettingsCopy[8:14]]
        try:
            logger.info(f"device is set to date: {datetime.datetime(year + 2000, month, day, hour, minute, second).strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            logger.warning(f"device is set to an invalid date")

        #write the current time into the cached settings which will be written later
        currentTime = datetime.datetime.now()
        setNewTimeDataBytes = timeSyncSettingsCopy[0:8]      #Take the first eight bytes from eeprom without modification
        setNewTimeDataBytes += bytes([currentTime.year - 2000, currentTime.month, currentTime.day, currentTime.hour, currentTime.minute, currentTime.second])
        setNewTimeDataBytes += bytes([sum(setNewTimeDataBytes) & 0xff, 0x00])           #first byte does not seem to matter, second byte is crc generated by sum over data and only using lower 8 bits
        self.cachedSettingsBytes[settingsTimeSyncSlice] = setNewTimeDataBytes
        
        logger.info(f"settings updated to new date {currentTime.strftime('%Y-%m-%d %H:%M:%S')}")
        return
        """