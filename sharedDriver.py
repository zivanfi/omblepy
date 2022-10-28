import logging
logger = logging.getLogger("omblepy")

class sharedDeviceDriverCode():
    #these need to be overwritten by device specific version
    deviceEndianess                 = None
    userStartAdressesList           = None
    perUserRecordsCountList         = None
    recordByteSize                  = None
    transmissionBlockSize           = None
    settingsReadAddress             = None
    settingsWriteAddress            = None
    settingsUnreadRecordsBytesSlice = None
    settingsTimeSyncBytesSlice      = None
    
    #abstract method, implemented by the device specific driver
    def deviceSpecific_ParseRecordFormat(self, singleRecordAsByteArray):
        raise NotImplementedError("Please Implement this method in the device specific file.")
    
    #abstract method, implemented by the device specific driver
    def deviceSpecific_syncWithSystemTime(self):
        raise NotImplementedError("Please Implement this method in the device specific file.")
    
    def _bytearrayBitsToInt(self, bytesArray, firstValidBitIdx, lastvalidBitIdx):
        bigInt = int.from_bytes(bytesArray, self.deviceEndianess)
        numValidBits = (lastvalidBitIdx-firstValidBitIdx) + 1
        shiftedBits = (bigInt>>(len(bytesArray) * 8 - (lastvalidBitIdx + 1)))
        bitmask = (2**(numValidBits)-1)
        return shiftedBits & bitmask
    
    def resetUnreadRecordsCounter(self):
        #special code for no new records is 0x8000
        unreadRecordsSettingsCopy = self.cachedSettingsBytes[self.settingsUnreadRecordsBytesSlice]
        resetUnreadRecordsBytes = (0x8000).to_bytes(2, byteorder=self.deviceEndianess)
        newUnreadRecordSettings = unreadRecordsSettingsCopy[:4] + resetUnreadRecordsBytes * 2 + unreadRecordsSettingsCopy[8:]
        self.cachedSettingsBytes[self.settingsUnreadRecordsBytesSlice] = newUnreadRecordSettings
    
    async def getRecords(self, btobj, useUnreadCounter, syncTime):
        await btobj.unlockWithUnlockKey()
        await btobj.startTransmission()
        
        #cache settings for time sync and for unread record counter
        self.cachedSettingsBytes = await btobj.readContinuousEepromData(self.settingsReadAddress, self.settingsTimeSyncBytesSlice.start)
        
        #hem7361 does likely not support reads with blocks crossing the boundary between the timeSyncSlice and the rest of the settings
        timeSyncNumBytes = self.settingsTimeSyncBytesSlice.stop - self.settingsTimeSyncBytesSlice.start
        self.cachedSettingsBytes += await btobj.readContinuousEepromData(self.settingsReadAddress + self.settingsTimeSyncBytesSlice.stop, timeSyncNumBytes)
        
        #maybe this could be combined into a single write
        if(syncTime):
            self.deviceSpecific_syncWithSystemTime()
            bytesToWrite = self.cachedSettingsBytes[self.settingsTimeSyncBytesSlice]
            await btobj.writeContinuousEepromData(self.settingsWriteAddress + self.settingsTimeSyncBytesSlice.start, bytesToWrite, btBlockSize = len(bytesToWrite))
        
        await btobj.endTransmission()
        return allUserRecordsList
    
    def calcRingBufferRecordReadLocations(self, userIdx, unreadRecords, lastWrittenSlot):
        userReadCommandsList = []
        if(lastWrittenSlot < unreadRecords): #two reads neccesary, because ring buffer start reached
            #read start of ring buffer
            firstRead = dict()
            firstRead["address"] = self.userStartAdressesList[userIdx]
            firstRead["size"]    = self.recordByteSize * lastWrittenSlot
            userReadCommandsList.append(firstRead)
            
            #read end of ring buffer
            secondRead = dict()
            secondRead["address"] = self.userStartAdressesList[userIdx]
            secondRead["address"] += (self.perUserRecordsCountList[userIdx] + lastWrittenSlot - unreadRecords) * self.recordByteSize
            secondRead["size"]    = self.recordByteSize * (unreadRecords - lastWrittenSlot)
            userReadCommandsList.append(secondRead)
        else:
            #read start of ring buffer
            firstRead = dict()
            firstRead["address"] = self.userStartAdressesList[userIdx]
            firstRead["address"] += self.recordByteSize * (lastWrittenSlot - unreadRecords)
            firstRead["size"]    = self.recordByteSize * unreadRecords
            userReadCommandsList.append(firstRead)
        return userReadCommandsList

    async def _getReadCommands_OnlyNewRecords(self):
        allUsersReadCommandsList = []
        readRecordsInfoByteArray = self.cachedSettingsBytes[self.settingsUnreadRecordsBytesSlice]
        numUsers = len(self.userStartAdressesList)
        for userIdx in range(numUsers):
            #byte location depends on endianess, so use _bytearrayBitsToInt to account for this
            lastWrittenSlotForUser = self._bytearrayBitsToInt(readRecordsInfoByteArray[2*userIdx+0:2*userIdx+2], 8, 15)
            unreadRecordsForUser   = self._bytearrayBitsToInt(readRecordsInfoByteArray[2*userIdx+4:2*userIdx+6], 8, 15)
            
            logger.info(f"Current ring buffer slot user{userIdx+1}: {lastWrittenSlotForUser}.")
            logger.info(f"Unread records user{userIdx+1}: {unreadRecordsForUser}.")
            readCmds = self.calcRingBufferRecordReadLocations(userIdx, unreadRecordsForUser, lastWrittenSlotForUser)
            allUsersReadCommandsList.append(readCmds)
        return allUsersReadCommandsList
    async def _getReadCommands_AllRecords(self):
        allUsersReadCommandsList = []
        for userIdx, userStartAddress in enumerate(self.userStartAdressesList):
            readCommand = dict()
            readCommand["address"] = userStartAddress
            readCommand["size"] = self.perUserRecordsCountList[userIdx] * self.recordByteSize
            singleUserReadCommands = [readCommand]
            allUsersReadCommandsList.append(singleUserReadCommands)
        return allUsersReadCommandsList