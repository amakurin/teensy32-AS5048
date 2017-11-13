#ifndef COMMANDS_h
#define COMMANDS_h
#include "as5048.h"
#include "utils.h"

enum USBCommand
{
    CMD_START_SENSORS,
    CMD_STOP,
    CMD_OTP_ZERO
};


class BaseCommand {
public:
    static const uint USB_PACKET_SIZE = 64;
    AS5048* _as5048;
    byte* _buffer;
    USBCommand _cmd_code;
    uint _write_counter;
    BaseCommand(AS5048* as5048, byte* buffer)
        :_as5048(as5048), _buffer(buffer), _write_counter(0) {
            _cmd_code = getCommandCode(buffer);
        };

    virtual ~BaseCommand(){};

    virtual void setup(){};
    
    virtual bool exec() = 0;

    static USBCommand getCommandCode(byte* data){
        return (USBCommand) data[0];
    }

    static uint getDataLen(byte* data){
        return (uint) data[1];
    }

    static void bufPrint(byte* data, uint data_len = USB_PACKET_SIZE){
        Serial.print(F("Buffer dump: "));
        for (uint i = 0; i< data_len; i++){
            Serial.print(data[i]);
            Serial.print(", ");
        }
        Serial.println();
    }

    uint getDataLen(){
        return getDataLen(_buffer);
    }

    void bufWrite(byte data){
        _buffer[_write_counter++] = data;
    }

    void bufWrite(void* data, uint data_len){
        for (uint i=0; i < data_len; i++){
            _buffer[i + _write_counter] = *((unsigned char*)(data)+i);
        }
        _write_counter += data_len;
    }

    void bufWriteStart(uint data_len, uint final_packet = 0){
        _write_counter = 0;
        bufWrite((byte) _cmd_code);
        bufWrite((byte) data_len);
        bufWrite((byte) final_packet);
    }

    void bufWriteEnd(){
        for (uint i=_write_counter; i < USB_PACKET_SIZE; i++){
            _buffer[i] = 0;
        }
        _write_counter = USB_PACKET_SIZE;
    }

    bool bufSend(){
        bufWriteEnd();
        int n = RawHID.send(_buffer, 100);
        return n > 0;
    }
    void bufPrint(){
        bufPrint(_buffer);
    }

};

class StartSensorsCommand:public BaseCommand {
public:

    TimeCounter _timeCounter;
    uint _updateCounter;
    uint _sendThre;

    StartSensorsCommand(AS5048* as5048, byte* buffer):BaseCommand(as5048, buffer){};
    ~StartSensorsCommand(){}

    void setup(){
        bufPrint();
        _as5048->setup();
        _updateCounter = 0;
        uint data_len = getDataLen();
        if (data_len>0) _sendThre = _buffer[2];
        else _sendThre = 100;
    }

    bool exec(){
        float sensor_data[2];
        sensor_data[0] = _as5048->readAngle();

Serial.println(sensor_data[0]);

        auto dt = _timeCounter.update();
        _updateCounter = (_updateCounter + 1) % _sendThre;
        if (_updateCounter == 0){
            sensor_data[1] = 1/dt;
            uint data_len = sizeof(sensor_data);
            bufWriteStart(data_len);
            bufWrite(sensor_data, data_len);
            bufSend();
        }
        return true;
    }
};

class GenericStopCommand:public BaseCommand {
public:
    GenericStopCommand(AS5048* as5048, byte* buffer):BaseCommand(as5048, buffer){};
    ~GenericStopCommand(){}

    void setup(){
    }

    bool exec() {
        bufWriteStart(1,1);
        bufWrite(1);
        bufSend();
        return false;
    }
};

class OTPZeroCommand:public BaseCommand {
public:
    OTPZeroCommand(AS5048* as5048, byte* buffer):BaseCommand(as5048, buffer){};
    ~OTPZeroCommand(){}

    void setup(){
        _as5048->setup();
    }

    bool exec() {
        bufWriteStart(1,1);
        bufWrite(1);
        bufSend();
        return false;
    }
};


#endif