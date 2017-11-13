#ifndef AS5048_h
#define AS5048_h

#include "Arduino.h"
#include <math.h>
#include "bus.h"
#include "utils.h"

class AS5048 {
public:
    static const uint8_t I2C_SLAVE_ADDR = 0x40;
    static const uint8_t REG_OTP_ZERO_HIGH = 0x16;
    static const uint8_t REG_OTP_ZERO_LOW  = 0x17;
    static const uint8_t REG_ANGLE_HIGH = 0xFE;

    const float degreesScale = 360./16383.;
    const float radiansScale = 2*M_PI/16383.;

    Bus* _bus;

    AS5048 (Bus* bus) : _bus(bus) {
        _bus->begin();
    }

    void setup(){
        writeRegister(REG_OTP_ZERO_HIGH, 0, 0);
        writeRegister(REG_OTP_ZERO_LOW, 0);

        uint8_t angle[2];
        readRegisters(REG_ANGLE_HIGH, 2, angle);

        writeRegister(REG_OTP_ZERO_HIGH, angle[0], 0);
        writeRegister(REG_OTP_ZERO_LOW, (angle[1] & 63));
    }

    float readAngle(bool inDegrees = false){
        uint8_t angle[2];
        readRegisters(REG_ANGLE_HIGH, 2, angle);
        return  ((inDegrees)? degreesScale : radiansScale) * ((angle[1] & 63) | (angle[0] << 6));
    }

    /********************************************************************
    UTILS
    *********************************************************************/
    bool writeRegister(uint8_t address, uint8_t data, uint8_t delay_ms = 1){
        bool res = _bus->writeByte(I2C_SLAVE_ADDR, address, data);
        delay(delay_ms);
        return res;
    }

    void readRegisters(uint8_t address, uint8_t count, uint8_t* dest){
        _bus->readBytes(I2C_SLAVE_ADDR, address, count, dest);
    }

    byte readRegister(uint8_t address){
        return _bus->readByte(I2C_SLAVE_ADDR, address);
    }


};

#endif